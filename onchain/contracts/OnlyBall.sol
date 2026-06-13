// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

/// Minimal TRC20 interface (FUDSX).
interface ITRC20 {
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/// @title OnlyBall — a fully on-chain daily 6/49 lottery paid in FUDSX.
/// @notice Tickets pull FUDSX into the contract (the jackpot escrow). After
/// `drawInterval` seconds anyone can call `executeDraw`, which picks 6 numbers
/// from block data, pays every ticket matching all six an equal share of the
/// pot, and rolls over the pot when there is no winner. Every ticket and draw
/// is emitted as an event and stored on-chain for full traceability.
/// @dev Randomness is derived from block data and is therefore only
/// pseudo-random (a block producer could in theory bias it). Adequate at this
/// scale; upgrade to an oracle for high-value pots.
contract OnlyBall {
    address public owner;
    ITRC20 public immutable fudsx;

    uint8 public constant PICKS = 6;
    uint8 public constant MAX_NUMBER = 49;

    uint256 public ticketPrice;   // FUDSX, 18 decimals
    uint256 public drawInterval;  // seconds between draws
    uint256 public currentRound;
    uint256 public nextDrawTime;  // epoch seconds
    uint256 public jackpotPool;   // FUDSX held for the live round (+ rollover)
    uint256 private nonce;

    struct Ticket {
        address player;
        uint8[6] numbers;
        uint64 mask; // bitmask of the 6 numbers, for O(1) matching
    }

    struct Draw {
        uint8[6] numbers;
        uint256 jackpot;
        uint256 winnerCount;
        uint256 drawnAt;
        bool done;
    }

    mapping(uint256 => Ticket[]) private roundTickets;
    mapping(uint256 => Draw) private roundDraw;
    mapping(address => uint256) public ticketsBought; // lifetime, per player

    event TicketPurchased(
        address indexed player,
        uint256 indexed round,
        uint8[6] numbers,
        string referralCode
    );
    event DrawCompleted(
        uint256 indexed round,
        uint8[6] winningNumbers,
        uint256 jackpot,
        uint256 winnerCount
    );
    event JackpotWon(address indexed winner, uint256 indexed round, uint256 amount);
    event Rollover(uint256 indexed round, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor(address _fudsx, uint256 _ticketPrice, uint256 _drawInterval) {
        require(_fudsx != address(0), "fudsx=0");
        require(_drawInterval > 0, "interval=0");
        owner = msg.sender;
        fudsx = ITRC20(_fudsx);
        ticketPrice = _ticketPrice;
        drawInterval = _drawInterval;
        currentRound = 1;
        nextDrawTime = block.timestamp + _drawInterval;
    }

    // --- Player actions ---------------------------------------------------

    /// Buy one ticket for the current round. Requires a prior FUDSX `approve`
    /// of `ticketPrice` to this contract. `referralCode` is emitted only for
    /// off-chain attribution.
    function buyTicket(uint8[6] calldata numbers, string calldata referralCode) external {
        uint64 mask = _validateAndMask(numbers);
        require(
            fudsx.transferFrom(msg.sender, address(this), ticketPrice),
            "FUDSX transferFrom failed"
        );
        jackpotPool += ticketPrice;
        roundTickets[currentRound].push(
            Ticket({player: msg.sender, numbers: numbers, mask: mask})
        );
        ticketsBought[msg.sender] += 1;
        emit TicketPurchased(msg.sender, currentRound, numbers, referralCode);
    }

    /// Pick the winning numbers and settle the round. Callable by anyone once
    /// `nextDrawTime` has passed (permissionless, so draws can't be censored).
    function executeDraw() external {
        require(block.timestamp >= nextDrawTime, "too early");
        uint256 round = currentRound;
        Ticket[] storage tickets = roundTickets[round];

        uint8[6] memory winning = _generateNumbers();
        uint64 winningMask = _toMask(winning);

        uint256 winnerCount = 0;
        uint256 n = tickets.length;
        for (uint256 i = 0; i < n; i++) {
            if (tickets[i].mask == winningMask) winnerCount++;
        }

        uint256 pot = jackpotPool;
        if (winnerCount > 0) {
            uint256 share = pot / winnerCount;
            for (uint256 i = 0; i < n; i++) {
                if (tickets[i].mask == winningMask) {
                    fudsx.transfer(tickets[i].player, share);
                    emit JackpotWon(tickets[i].player, round, share);
                }
            }
            // Distributed `share * winnerCount`; any rounding dust rolls over.
            jackpotPool = pot - share * winnerCount;
        } else {
            emit Rollover(round, pot);
            // Pot stays in `jackpotPool` and carries into the next round.
        }

        roundDraw[round] = Draw({
            numbers: winning,
            jackpot: pot,
            winnerCount: winnerCount,
            drawnAt: block.timestamp,
            done: true
        });
        emit DrawCompleted(round, winning, pot, winnerCount);

        currentRound = round + 1;
        nextDrawTime = block.timestamp + drawInterval;
        unchecked {
            nonce++;
        }
    }

    // --- Views ------------------------------------------------------------

    function getTimeUntilDraw() external view returns (uint256) {
        if (block.timestamp >= nextDrawTime) return 0;
        return nextDrawTime - block.timestamp;
    }

    function getRoundTicketCount(uint256 round) external view returns (uint256) {
        return roundTickets[round].length;
    }

    function getTicket(uint256 round, uint256 index)
        external
        view
        returns (address player, uint8[6] memory numbers)
    {
        Ticket storage t = roundTickets[round][index];
        return (t.player, t.numbers);
    }

    function getDraw(uint256 round)
        external
        view
        returns (
            uint8[6] memory numbers,
            uint256 jackpot,
            uint256 winnerCount,
            uint256 drawnAt,
            bool done
        )
    {
        Draw storage d = roundDraw[round];
        return (d.numbers, d.jackpot, d.winnerCount, d.drawnAt, d.done);
    }

    // --- Internal ---------------------------------------------------------

    function _validateAndMask(uint8[6] calldata numbers) internal pure returns (uint64) {
        uint64 mask = 0;
        for (uint256 i = 0; i < PICKS; i++) {
            uint8 num = numbers[i];
            require(num >= 1 && num <= MAX_NUMBER, "number out of range");
            uint64 bit = uint64(1) << num;
            require(mask & bit == 0, "duplicate number");
            mask |= bit;
        }
        return mask;
    }

    function _generateNumbers() internal view returns (uint8[6] memory result) {
        uint64 mask = 0;
        uint256 count = 0;
        uint256 seed = uint256(
            keccak256(
                abi.encodePacked(
                    blockhash(block.number - 1),
                    block.timestamp,
                    currentRound,
                    nonce,
                    jackpotPool,
                    address(this)
                )
            )
        );
        uint256 i = 0;
        while (count < PICKS) {
            uint8 num = uint8(uint256(keccak256(abi.encodePacked(seed, i))) % MAX_NUMBER) + 1;
            uint64 bit = uint64(1) << num;
            if (mask & bit == 0) {
                mask |= bit;
                result[count] = num;
                count++;
            }
            unchecked {
                i++;
            }
        }
        // Insertion sort (6 elements) so numbers are returned ascending.
        for (uint256 a = 1; a < PICKS; a++) {
            uint8 key = result[a];
            uint256 b = a;
            while (b > 0 && result[b - 1] > key) {
                result[b] = result[b - 1];
                b--;
            }
            result[b] = key;
        }
    }

    function _toMask(uint8[6] memory numbers) internal pure returns (uint64) {
        uint64 mask = 0;
        for (uint256 i = 0; i < PICKS; i++) {
            mask |= uint64(1) << numbers[i];
        }
        return mask;
    }

    // --- Owner controls ---------------------------------------------------

    function setTicketPrice(uint256 newPrice) external onlyOwner {
        ticketPrice = newPrice;
    }

    function setDrawInterval(uint256 newInterval) external onlyOwner {
        require(newInterval > 0, "interval=0");
        drawInterval = newInterval;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "newOwner=0");
        owner = newOwner;
    }

    /// Recover tokens accidentally sent here that are not part of the pot.
    function rescueExcess(address to) external onlyOwner {
        require(to != address(0), "to=0");
        uint256 bal = fudsx.balanceOf(address(this));
        require(bal > jackpotPool, "no excess");
        fudsx.transfer(to, bal - jackpotPool);
    }
}
