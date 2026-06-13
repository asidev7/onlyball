export {};

declare global {
  interface TronWebDefaultAddress {
    base58: string | false;
    hex: string | false;
  }

  type TronContractInstance = Record<
    string,
    (...args: unknown[]) => {
      call: (options?: Record<string, unknown>) => Promise<unknown>;
      send: (options?: Record<string, unknown>) => Promise<string>;
    }
  >;

  interface TronWebInstance {
    defaultAddress: TronWebDefaultAddress;
    ready?: boolean;
    fullNode?: { host: string };
    contract: (abi?: unknown[]) => {
      at: (address: string) => Promise<TronContractInstance>;
    };
    trx: { getBalance: (address?: string) => Promise<number> };
    address: { fromHex: (hex: string) => string; toHex: (b58: string) => string };
    isAddress: (address: string) => boolean;
  }

  interface TronLinkProvider {
    request: (args: { method: string; params?: unknown }) => Promise<unknown>;
    ready?: boolean;
    tronWeb?: TronWebInstance;
  }

  interface Window {
    tronWeb?: TronWebInstance;
    tronLink?: TronLinkProvider;
    tokenpocket?: unknown;
    bitkeep?: { tronLink?: TronLinkProvider };
  }
}
