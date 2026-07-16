# PROMPT.md — ONLYBALL : Loterie quotidienne $BALL (version simple, sans smart contract)

> **Instruction pour l'agent de code (Claude Code / Cursor)** : Construis cette application web Django complète, de bout en bout. Version SIMPLE : pas de programme Solana à déployer, tout est géré par le backend avec un algorithme de tirage **provably fair**. Respecte STRICTEMENT le stack, le design et la conformité.

---

## 1. CONCEPT

**OnlyBall** est une loterie quotidienne inspirée de `https://powerball.tech/` :

- L'utilisateur crée un compte avec **email** OU se connecte avec son **wallet** (Trust Wallet, Phantom, MetaMask via WalletConnect).
- Il **recharge son compte en USDT** en envoyant vers une adresse de dépôt.
- Il achète des **$BALL** : **10 USDT = 100 $BALL** (taux configurable).
- **100 $BALL = 1 ticket** pour le tirage du soir. 500 $BALL = 5 tickets, 1 000 $BALL = 10 tickets. **Aucun plafond.**
- **Tirage chaque nuit à minuit, heure de l'Est US (America/New_York)** — countdown « NEXT DRAWING » permanent qui repart pour 24 h après chaque tirage.
- Un **algorithme provably fair** (commit-reveal, voir §5) choisit un ticket gagnant.
- Le gagnant reçoit le **jackpot en USDT** sur son wallet, automatiquement.

⚠️ **$BALL est ici un solde interne** (ledger en base de données), PAS un token onchain. Aucun smart contract à écrire ni déployer. Seuls les dépôts et retraits USDT touchent la blockchain.

---

## 2. STACK TECHNIQUE (VERROUILLÉ)

| Couche | Technologie |
|---|---|
| Backend | **Django 5** (Python 3.12) |
| Base de données | **PostgreSQL** |
| CSS | **Tailwind CSS via CDN** |
| Interactivité | **Alpine.js** (CDN) |
| Tâches planifiées | **Celery + Redis** (détection dépôts, tirage, payout) |
| Blockchain (lecture/envoi seulement) | USDT **SPL sur Solana** via `solana-py` + `solders` (RPC public). Option TRC20 en v2. |
| Auth wallet | Signature de message (nonce) — Phantom/Solflare natif, **Trust Wallet & MetaMask via WalletConnect v2** |

### Design system — MÊME STYLE QUE POWERBALL.TECH
- **Fond crème `#FBF5E7`** sur tout le site (theme-color identique à powerball.tech).
- Texte principal noir `#111111`, secondaire `#555555`.
- **Accent rouge boule de loterie `#E4002B`** (boutons principaux, montant du jackpot), accent secondaire bleu `#0048AE`.
- **Design flat rétro-loterie** : AUCUN gradient, AUCUNE ombre. Bordures noires fines `border border-black/10`, coins `rounded-2xl`.
- Élément visuel signature : une **boule rouge avec le chiffre à l'intérieur** (SVG inline : cercle rouge `#E4002B`, texte blanc centré) utilisée pour les numéros d'étapes 01/02/03 et le logo.
- Logo texte : **ONLYBALL** en `font-extrabold tracking-tight`, avec la boule rouge en « O ».
- Typographie : `Inter` ou `Space Grotesk` (Google Fonts). Jackpot et countdown en `tabular-nums text-6xl md:text-8xl font-extrabold`.
- **Icônes : SVG inline uniquement.** Pour les wallets, utiliser les **VRAIS logos officiels en SVG inline** :
  - Trust Wallet (bouclier bleu officiel)
  - Phantom (fantôme violet officiel)
  - MetaMask (renard orange officiel)
  - USDT/Tether (cercle vert `#26A17B` avec ₮ blanc)
  - Solana (les 3 barres, ok en monochrome noir)
  Récupérer les SVG officiels depuis les press kits / brand assets de chaque projet et les intégrer inline. INTERDICTION d'utiliser des emojis ou des icônes génériques à la place des logos de marques.
- **Mobile-first**, conteneur `max-w-5xl mx-auto px-4`.

---

## 3. STRUCTURE DE LA PAGE D'ACCUEIL (copie de powerball.tech)

Une seule longue page `/` + pages fonctionnelles. Sections dans cet ordre :

1. **Header** fixe : logo ONLYBALL à gauche, à droite « Sign in » + bouton rouge « Connect Wallet ».
2. **Hero** :
   - Petit label « DAILY DRAWING — MIDNIGHT ET »
   - **Montant du jackpot** énorme : `$12,450 USDT` (dynamique)
   - **NEXT DRAWING** : countdown `HH:MM:SS` géant, alimenté par `/api/next-draw/` (jamais codé en dur)
   - Deux boutons : « Get $BALL » (rouge) et « How it works » (contour noir)
3. **How it works — 3 étapes numérotées avec boules rouges** :
   - **01 — Hold $BALL** : « Every 100 $BALL in your account earns one ticket in tonight's drawing. »
   - **02 — More tokens, more entries** : « 500 = 5 tickets. 1,000 = 10. There's no cap. Sign up with email or wallet. »
   - **03 — Drawn at midnight ET** : « A provably fair algorithm picks one ticket. The winner is paid automatically in USDT. »
4. **Last winners** : tableau des 10 derniers tirages (date, adresse/pseudo tronqué, jackpot, lien preuve).
5. **Provably fair** : explication courte + lien vers `/fair`.
6. **Stats** : total tickets ce soir, joueurs, USDT distribués.
7. **FAQ** (accordéon Alpine.js).
8. **Footer** : liens Legal, Fair, FAQ, disclaimer 18+.

Version FR/EN : textes en anglais par défaut (comme powerball.tech), i18n Django prêt pour le français.

---

## 4. FLUX UTILISATEUR

### Inscription / connexion (double mode)
- **Email** : email + mot de passe + date de naissance (18+ bloquant), vérification email.
- **Wallet** : bouton « Connect Wallet » → modal Alpine.js listant Trust Wallet / Phantom / MetaMask (vrais logos SVG) → signature d'un nonce → compte créé/connecté automatiquement avec l'adresse comme identifiant. Un compte email peut lier un wallet ensuite (obligatoire pour recevoir les gains).

### Recharge USDT (simple)
- Page `/deposit` : le système affiche **UNE adresse de dépôt USDT (SPL) unique par utilisateur** (dérivée d'un wallet maître HD, index stocké en base) + QR code SVG généré côté serveur.
- Worker Celery toutes les 30 s : scanne les adresses de dépôt via RPC, crédite `usdt_balance` après N confirmations, enregistre le tx hash.
- Les fonds sont balayés (sweep) périodiquement vers le wallet trésorerie.

### Achat de $BALL
- Page `/buy` : slider/input USDT → conversion en direct (Alpine.js) → confirmation → débit `usdt_balance`, crédit `ball_balance`. Répartition de chaque achat : **70 % jackpot du soir, 20 % rollover, 10 % frais plateforme** (configurable, affiché publiquement).

### Tickets
- `tickets = floor(ball_balance / 100)` — recalculé et **figé au snapshot de 23h50 ET** chaque soir. Les $BALL ne sont pas consommés : les détenir donne droit au tirage chaque nuit (comme powerball.tech).

### Gain & retrait
- Le gagnant reçoit automatiquement le jackpot en USDT sur son **wallet lié** (envoi onchain par le worker payout, tx hash publié). S'il n'a pas de wallet lié : jackpot crédité sur son solde interne + email l'invitant à retirer.
- Page `/withdraw` : retrait USDT vers n'importe quelle adresse (min 5 USDT, KYC au-delà du seuil).

---

## 5. ALGORITHME DE TIRAGE PROVABLY FAIR (cœur du système)

Sans smart contract, la confiance repose sur ce mécanisme — l'implémenter EXACTEMENT :

1. **Commit (avant le tirage)** : chaque jour à l'ouverture du tirage (00h01 ET), le serveur génère un `server_seed` aléatooire (32 bytes, `secrets.token_bytes`). Il publie immédiatement `server_seed_hash = SHA256(server_seed)` sur la page `/fair` et dans l'API. Impossible de changer le seed ensuite sans que le hash ne corresponde plus.
2. **Snapshot (23h50 ET)** : liste ordonnée des tickets figée : `[(user_id, ticket_start, ticket_end), ...]`, triée par `user_id`. Publier `snapshot_hash = SHA256(json_canonique_du_snapshot)`.
3. **Beacon public (minuit ET)** : récupérer une valeur aléatoire publique et invérifiable à l'avance : le **blockhash du dernier bloc Solana finalisé après 00:00:00 ET** (`beacon`). Enregistrer le slot et le blockhash.
4. **Tirage** : `winning_number = int(HMAC_SHA256(key=server_seed, msg=snapshot_hash + beacon), 16) % total_tickets` → le ticket gagnant → le user gagnant.
5. **Reveal** : publier immédiatement `server_seed`, `beacon` (slot + blockhash), `snapshot_hash`, le JSON du snapshot (adresses pseudonymisées), `winning_number`, et le **tx hash du paiement**.
6. **Page `/fair`** : explication + **vérificateur intégré** (Alpine.js, crypto en JS via SubtleCrypto) où n'importe qui recalcule le résultat, + un script Python de vérification téléchargeable.

Chaque `Draw` en base conserve tous ces éléments de façon immuable (champs non modifiables après statut `drawn`).

---

## 6. MODÈLES DJANGO (app `core`)

```python
User(AbstractUser)        # email nullable si wallet-only, birth_date, kyc_status, is_self_excluded
WalletLink                # user FK, address unique, chain='solana', provider, verified_at
DepositAddress            # user OneToOne, address, derivation_index
LedgerEntry               # user, type(deposit/buy_ball/win/withdraw/fee), usdt_delta, ball_delta, ref, tx_hash — journal comptable append-only, soldes = somme
Draw                      # date, server_seed_hash, server_seed(reveal), snapshot_hash, beacon_slot, beacon_blockhash, total_tickets, winning_number, winner FK, jackpot_usdt, payout_tx, status
TicketSnapshot            # draw FK, user FK, ball_balance, ticket_start, ticket_end
WithdrawalRequest         # user, address, amount, status, tx_hash
Config (singleton)        # ball_price_usdt=0.10, ticket_threshold=100, jackpot_bps=7000, rollover_bps=2000, fee_bps=1000, min_withdraw=5
ConfigChangeLog           # audit immuable
```

Règle d'or : **jamais de champ `balance` modifié directement** — tout passe par `LedgerEntry` en transaction atomique (`select_for_update`).

---

## 7. PAGES & API

Pages : `/` (home longue), `/deposit`, `/buy`, `/account` (soldes, tickets ce soir, historique, wallets, jeu responsable), `/withdraw`, `/draws` (historique), `/fair` (vérificateur), `/legal`, admin Django.

API JSON :
- `GET /api/next-draw/` → `{scheduled_at_utc, jackpot_usdt, total_tickets, server_seed_hash}`
- `GET /api/me/tickets/`
- `POST /api/wallet/nonce/` + `POST /api/wallet/verify/`
- `GET /api/draws/<id>/` → toutes les données de vérification

Celery beat (fuseau `America/New_York` via `zoneinfo`, DST géré automatiquement) :
- `*/30s` scan des dépôts · `23:50` snapshot · `00:00` beacon + tirage + payout · `00:01` commit du seed du tirage suivant.

---

## 8. CONFORMITÉ (OBLIGATOIRE)

Loterie en argent réel = activité réglementée. Le code DOIT inclure :
1. **18+** bloquant à l'inscription + bandeau permanent « 18+. Play responsibly. »
2. **Geo-blocking** middleware (liste `BLOCKED_COUNTRIES`, USA inclus par défaut).
3. **KYC** au-delà de 100 USDT de dépôts cumulés ou avant tout retrait > 100 USDT.
4. **Jeu responsable** : auto-exclusion 7/30/90 jours, plafond de dépôt hebdomadaire personnel.
5. Page `/legal` complète, probabilités réelles affichées (`vos tickets / tickets totaux`), aucune promesse de gain.
6. `ConfigChangeLog` immuable pour tout changement de taux/répartition.

> Ne pas mettre en production avec de l'argent réel sans licence de jeux valide dans la juridiction d'exploitation.

---

## 9. VARIABLES D'ENVIRONNEMENT

```
SITE_NAME=OnlyBall
SOLANA_RPC_URL=
USDT_MINT=Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB
MASTER_WALLET_MNEMONIC=        # jamais commité
TREASURY_ADDRESS=
DEPOSIT_CONFIRMATIONS=32
BALL_PRICE_USDT=0.10
TICKET_THRESHOLD=100
JACKPOT_BPS=7000
ROLLOVER_BPS=2000
FEE_BPS=1000
BLOCKED_COUNTRIES=US
DATABASE_URL=
REDIS_URL=
```

---

## 10. LIVRABLES & DEFINITION OF DONE

1. Projet Django complet + migrations + fixtures démo (faux tirages passés pour la section winners).
2. Workers Celery + beat schedule ET.
3. Page `/fair` avec vérificateur fonctionnel (JS + script Python).
4. Tests : ledger atomique, calcul tickets, algorithme de tirage (vecteurs de test fixes), timezone ET/DST, geo-block, auto-exclusion.
5. `README.md` avec installation, mode TESTNET (devnet + faux USDT) et checklist légale avant mainnet.

**Done quand** : un utilisateur s'inscrit par email OU Trust Wallet, dépose de l'USDT (devnet), achète 100 $BALL pour 10 USDT, voit « 1 ticket » et le countdown NEXT DRAWING, le tirage de minuit ET s'exécute, le gagnant est payé et n'importe qui peut vérifier le résultat sur `/fair`.
