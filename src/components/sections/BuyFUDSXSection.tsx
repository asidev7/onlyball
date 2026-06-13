import BuyFUDSXForm from "@/components/buy/BuyFUDSXForm";

export default function BuyFUDSXSection() {
  return (
    <section className="bg-white">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2">
        <div>
          <h2 className="font-head text-3xl font-semibold text-[#0D0D0D] sm:text-4xl">
            Get FUDSX to play
          </h2>
          <p className="mt-3 max-w-md font-body text-sm text-[#6B7280]">
            FUDSX is the fuel of OnlyBall. The rate is fixed by the protocol:
            <span className="font-semibold text-[#0D0D0D]">
              {" "}
              1 USDT = 10 FUDSX
            </span>
            . Your unspent FUDSX always stays in your wallet — ready for the next
            round.
          </p>
          <ul className="mt-6 space-y-2 font-body text-sm text-[#6B7280]">
            <li>• Approve USDT (TRC20), then receive FUDSX instantly.</li>
            <li>• Minimum to play: 200 FUDSX (≈ 20 USDT).</li>
            <li>• No lock-up — swap back on SunSwap any time.</li>
          </ul>
        </div>

        <div className="rounded-[12px] border border-black/10 bg-white p-6 text-[#0D0D0D]">
          <BuyFUDSXForm light />
        </div>
      </div>
    </section>
  );
}
