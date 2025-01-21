I have been working on designing a Rock paper scissor game with a bit of a twist. I'd like help resolving basic move processing working, and then I'd like help implementing the upgrade plugin. Let's do one at a time

Core rules and context follow: 
Core Game Requirements:
1. Players start with:
   - 20 health points
   - 0 chaos points
   - 50 coins

2. Win conditions (first to achieve any):
   - Win 3 out of 5 rounds
   - Reach 10 chaos points
   - Deplete opponent's health (starting at 20)

3. Round Structure:
   - Players simultaneously choose rock/paper/scissors
   - Losing player loses 7 health points
   - Both players receive 15 coins after each round
   - Round results must be tracked in game state

4. Player Turn Flow:
   - Both players make moves simultaneously
   - After round resolution, players can purchase upgrades

A previous version of your code helped design some of the upgrade plug-in logic which I can provide more extensive detail on if needed but I'll provide the high-level project files that are most important; right now -- 
Here's the current file tree with brief descriptions:
.
├── backend/
│   ├── game.ts           # Main boardgame.io game logic and state definitions
│   ├── package-lock.json # Node dependencies lock file
│   ├── plugins/          # Custom boardgame.io plugins
│   │   └── upgrades/     # Plugin for handling upgrade purchases
│   └── server.ts         # boardgame.io server setup and configuration
│
└── src/
    ├── app/
    │   ├── layout.tsx    # Root Next.js layout component
    │   ├── page.tsx      # Home page component
    │   └── rps/
    │       └── page.tsx  # Rock Paper Scissors game page component
    └── hooks/
        └── use-toast.ts  # Custom hook for showing toast notifications
Recent Game Logic Changes & Issues:
Move Submission System:
Implemented makeMoveAction to handle player move submissions
Added type safety for the move action function
Moves are being recorded in G.moveSubmissions and G.players[playerID].currentMove
Phase Transitions:
Added phase transition from moveSelection to resolution when both players submit moves
Initially had type errors with endIf function return type
Fixed by returning proper { next: 'resolution' } object
Current Issues:
Round resolution wasn't triggering automatically after moves
Added logging to track phase transitions
Fixed phase transition logic with proper endIf condition
Game Flow:
moveSelection Phase
  └─> Both players submit moves
      └─> Resolution Phase (resolves round)
          └─> Purchase Upgrades Phase
              └─> Back to moveSelection
The main challenge has been getting the automatic phase transitions to work properly after both players submit their moves. We've added logging and fixed the phase transition logic, but should monitor to ensure rounds are being resolved correctly.

key game files: 
backend/game.ts
import { Game, Ctx } from 'boardgame.io';
import { INVALID_MOVE } from 'boardgame.io/core';
import { UpgradePlugin } from './plugins/upgrades/index';

//
// 1) Define a custom simultaneously-played turn order.
//
const SIMULTANEOUS_ORDER = {
  // first => set position 0, ignoring any default round-robin logic
  first: () => 0,
  // next => return undefined so the turn does not advance automatically
  next: () => undefined,
  // playOrder => array of all players
  playOrder: ({ G, ctx }: { G: any; ctx: Ctx }) => Object.keys(G.players),
};

/**
 * Represents the portion of G for each player's data.
 */
interface PlayerState {
  health: number;
  chaos: number;
  coins: number;
  wins: number;       // how many ro unds this player has won
  currentMove?: string | null; // "rock" | "paper" | "scissors" | undefined
}

/**
 * The overall structure of G (game state).
 */
export interface RPSState {
  players: Record<string, PlayerState>;
  roundCount: number;
  roundHistory: {
    player0Move: string;
    player1Move: string;
    winner?: string; // "0" | "1" | "draw"
  }[];
  // Track each player's move submission for debugging/validation
  moveSubmissions: Record<string, string>;
  gameOver?: boolean;
  winner?: string;
}

/**
 * Helper function to resolve a single RPS matchup.
 * Returns "0" if player0 wins, "1" if player1 wins, or "draw" if tie.
 */
function resolveRPS(moveA: string, moveB: string): '0' | '1' | 'draw' {
  if (moveA === moveB) return 'draw';

  if (
    (moveA === 'rock' && moveB === 'scissors') ||
    (moveA === 'paper' && moveB === 'rock') ||
    (moveA === 'scissors' && moveB === 'paper')
  ) {
    return '0';
  }
  return '1';
}

/**
 * Resolves a round of RPS combat using the current moves.
 */
function resolveRound(G: RPSState, ctx: Ctx): void {
  // Get both players' moves
  const player0Move = G.players['0'].currentMove;
  const player1Move = G.players['1'].currentMove;

  if (!player0Move || !player1Move) {
    return; // Can't resolve if moves aren't set
  }

  // Determine winner
  const result = resolveRPS(player0Move, player1Move);

  // Record the round in history
  G.roundHistory.push({
    player0Move,
    player1Move,
    winner: result
  });

  // Update player stats based on result
  if (result === '0') {
    G.players['0'].wins++;
    G.players['1'].health -= 1; // Example: loser takes damage
  } else if (result === '1') {
    G.players['1'].wins++;
    G.players['0'].health -= 1;
  }

  // Reset moves for next round
  G.players['0'].currentMove = null;
  G.players['1'].currentMove = null;
  G.moveSubmissions = {};

  // Increment round counter
  G.roundCount++;
}

/**
 * Checks for game-end conditions:
 * 1) 3 out of 5 round wins
 * 2) 10 chaos points
 * 3) Opponent's health <= 0
 */
function checkGameEnd(G: RPSState): { winner?: string; draw?: boolean } | undefined {
  const p0 = G.players['0'];
  const p1 = G.players['1'];

  // Check wins
  if (p0.wins === 3) return { winner: '0' };
  if (p1.wins === 3) return { winner: '1' };

  // Check chaos points
  if (p0.chaos >= 10) return { winner: '0' };
  if (p1.chaos >= 10) return { winner: '1' };

  // Check Health
  if (p0.health <= 0 && p1.health <= 0) {
    // both died => "draw" scenario
    return { draw: true };
  }
  if (p0.health <= 0) {
    return { winner: '1' };
  }
  if (p1.health <= 0) {
    return { winner: '0' };
  }

  return undefined; // no immediate winner
}

/**
 * Validate if a move is allowed.
 */
function validateMove(context: any, choice: string): boolean {
  const { G, ctx, playerID } = context;
  
  // Check if player is active
  if (!playerID || !ctx.activePlayers?.[playerID]) {
    console.warn('Move invalid: Player not active:', {
      playerID,
      activePlayers: ctx.activePlayers
    });
    return false;
  }

  // Check if player already moved
  if (G.players[playerID].currentMove !== null) {
    console.warn('Move invalid: Player already moved:', playerID);
    return false;
  }

  if (!['rock', 'paper', 'scissors'].includes(choice)) {
    console.warn('Move invalid: Invalid choice:', choice);
    return false;
  }

  return true;
}

// Define moves as standalone functions first
const selectMove = (context: any, choice: string) => {
  console.log('>>> selectMove called by Player:', context.playerID, ' choice=', choice);
  const { G, ctx, playerID } = context;
  if (!playerID) return INVALID_MOVE;
  if (!validateMove(context, choice)) {
    return INVALID_MOVE;
  }

  if (!G.moveSubmissions) {
    G.moveSubmissions = {};
  }
  G.moveSubmissions[playerID] = choice;

  // in favor of commitMoves, so no direct effect here
};

const commitMoves = (context: any) => {
  console.log('>>> commitMoves called by Player:', context.playerID);
  const { G, ctx, events } = context;
  const p0Move = G.players['0'].currentMove;
  const p1Move = G.players['1'].currentMove;
  
  if (!p0Move || !p1Move) {
    return INVALID_MOVE;
  }

  const result = resolveRPS(p0Move, p1Move);

  // Apply health reduction and update wins
  if (result === '0') {
    // Player 0 wins this round
    G.players['1'].health -= 7; // losing player loses 7 health
    G.players['0'].wins += 1;
  } else if (result === '1') {
    // Player 1 wins this round
    G.players['0'].health -= 7; // losing player loses 7 health 
    G.players['1'].wins += 1;
  }
  // draw => no health change and no wins

  // Both players gain 15 coins
  G.players['0'].coins += 15;
  G.players['1'].coins += 15;

  // Chaos points: winner gets +2, loser +3
  if (result === '0') {
    G.players['0'].chaos += 2;
    G.players['1'].chaos += 3;
  } else if (result === '1') {
    G.players['1'].chaos += 2;
    G.players['0'].chaos += 3;
  } else {
    // draw
    G.players['0'].chaos += 1;
    G.players['1'].chaos += 1;
  }

  // Record the round result
  G.roundHistory.push({
    player0Move: p0Move,
    player1Move: p1Move,
    winner: result,
  });

  // Clear moves for next round
  G.players['0'].currentMove = null;
  G.players['1'].currentMove = null;

  // Check for game over condition
  if (G.players['0'].health <= 0 || G.players['1'].health <= 0) {
    G.gameOver = true;
    G.winner = G.players['0'].health <= 0 ? '1' : '0';
    events?.endGame?.();
  } else {
    // Continue to next phase if game isn't over
    events?.endPhase?.();
  }
};

const buyStuff = ({ G, playerID }: any, cost: number) => {
  if (!playerID) return INVALID_MOVE;
  if (cost > G.players[playerID].coins) {
    return INVALID_MOVE;
  }
  // This is where you would apply "upgrades".
  // Decrement coins for now:
  G.players[playerID].coins -= cost;
};

const endPurchase = ({ events }: any) => {
  events?.endPhase?.();
};

const makeMoveAction = ({ G, playerID }: { G: RPSState; playerID: string }, move: string) => {
  if (!playerID) return INVALID_MOVE;
  G.players[playerID].currentMove = move;
  G.moveSubmissions[playerID] = move;
};

/**
 * Create the game configuration.
 */
export const RPSGame: Game<RPSState> = {
  name: 'rps-game',

  setup: () => ({
    players: {
      '0': { health: 3, chaos: 0, coins: 0, wins: 0, currentMove: null },
      '1': { health: 3, chaos: 0, coins: 0, wins: 0, currentMove: null }
    },
    roundCount: 0,
    roundHistory: [],
    moveSubmissions: {}
  }),

  /**
   * We will have two phases:
   * 1) "moveSelection": players simultaneously choose R/P/S
   * 2) "purchaseUpgrades": placeholder for potential upgrad hourses logic
   */
  phases: {
    moveSelection: {
      start: true,
      moves: {
        makeMove: {
          move: makeMoveAction,
          client: false
        }
      },
      endIf: ({ G }) => {
        // Check if both players have submitted moves
        const bothMoved = Boolean(G.players['0'].currentMove && G.players['1'].currentMove);
        if (bothMoved) {
          return { next: 'resolution' };
        }
        return false;
      },
      next: 'resolution',
      turn: {
        activePlayers: { all: 'select' },
        stages: {
          select: {
            moves: {
              makeMove: makeMoveAction
            }
          }
        }
      }
    },
    purchaseUpgrades: {
      moves: {
        purchaseUpgrade: (G, ctx, upgradeId) => {
          const ok = ctx.plugins.upgrades.purchaseUpgrade(upgradeId);
          if (!ok) {
            return INVALID_MOVE;
          }
        }
      },
      next: 'moveSelection'
    },
    resolution: {
      onBegin: (context) => {
        const { G, ctx } = context;
        console.log('Resolution phase started', {
          moves: G.moveSubmissions,
          phase: ctx.phase
        });
        resolveRound(G, ctx);
      },
      onEnd: (context) => {
        const { G, ctx, events } = context;
        console.log('Resolution phase ended', {
          roundHistory: G.roundHistory,
          phase: ctx.phase
        });
        if (!checkGameEnd(G)) {
          events.setPhase('purchaseUpgrades');
        }
      }
    }
  },

  /**
   * We define the stage-based moves below using the "turn" -> "stages" structure.
   * Because we use 'activePlayers' at the phase level, the same stage can apply to all players.
   */
  turn: {
    minMoves: 1,
    maxMoves: 1,
    onBegin: (context) => {
      const { G, ctx, playerID } = context;
      console.log('Turn began:', {
        currentPlayer: ctx.currentPlayer,
        phase: ctx.phase,
        activePlayers: ctx.activePlayers,
        playerID
      });
    },
    onMove: (context) => {
      const { G, ctx } = context;
      console.log('Move made:', {
        currentPlayer: ctx.currentPlayer,
        moveSubmissions: G.moveSubmissions,
        activePlayers: ctx.activePlayers
      });
    }
  },

  // The game ends if checkGameEnd returns a result
  endIf: (context) => {
    const { G } = context;
    return checkGameEnd(G);
  },

  plugins: [
    new UpgradePlugin()
  ],
}; 

plugins/upgrades/index.ts
import type { Plugin as PluginType } from 'boardgame.io';
import { Ctx } from 'boardgame.io';
import type { Game, FnContext } from 'boardgame.io';
import type { GameMethod } from 'boardgame.io/core';
import { UpgradeState, Upgrade } from './types';
import { upgradeRegistry } from './registry';

interface PluginContext {
  data: UpgradeState;
  playerID?: string;
  G: any;
  ctx: Ctx;
  game: Game;
  [key: string]: unknown;
}

export class UpgradePlugin implements PluginType {
  name = 'upgrades';

  setup(): UpgradeState {
    return {
      available: [],
      active: {},
      history: {},
    };
  }

  api(context: PluginContext) {
    const { data, playerID, G } = context;
    return {
      purchaseUpgrade: (upgradeId: string): boolean => {
        const upgrade = data.available.find((u: Upgrade) => u.id === upgradeId);
        if (!upgrade || !playerID) return false;

        const player = G.players[playerID];
        if (!player || player.coins < upgrade.cost) return false;

        // Subtract cost & add chaos to the player's state
        player.coins -= upgrade.cost;
        player.chaos += upgrade.chaosPoints;

        if (!data.active[playerID]) {
          data.active[playerID] = {};
        }
        data.active[playerID][upgradeId] = {
          remainingDuration:
            typeof upgrade.duration === 'number'
              ? upgrade.duration
              : upgrade.duration === 'permanent'
              ? -1
              : 1,
          acquired: Date.now(),
        };

        if (!data.history[playerID]) {
          data.history[playerID] = [];
        }
        data.history[playerID].push(upgradeId);

        return true;
      },
    };
  }

  fnWrap(moveOrHook: Function, methodType: GameMethod) {
    return (context: FnContext, ...args: unknown[]) => {
      const { G, ctx } = context;
      const data = context.data as UpgradeState;

      // If we're entering the 'purchaseUpgrades' phase, generate new upgrades if needed.
      if (ctx.phase === 'purchaseUpgrades') {
        if (G?.roundHistory?.length) {
          const lastRound = G.roundHistory[G.roundHistory.length - 1];
          if (lastRound) {
            const pMove = lastRound[`player${ctx.currentPlayer}Move`];
            data.available = selectRandomUpgrades(pMove, 3);
          }
        }
      }
      return moveOrHook(context, ...args);
    };
  }
}

function selectRandomUpgrades(moveType: 'rock' | 'paper' | 'scissors', count: number): Upgrade[] {
  const filtered = upgradeRegistry.filter((u) => u.moveType === moveType);
  return shuffle(filtered).slice(0, count);
}

function shuffle<T>(array: T[]): T[] {
  return [...array].sort(() => Math.random() - 0.5);
} 

plugins/upgrades/registry.ts
import { Upgrade } from './types';

export const upgradeRegistry: Upgrade[] = [
  {
    id: 'rock_reinforcement',
    name: 'Rock Reinforcement',
    cost: 3,
    moveType: 'rock',
    chaosPoints: 1,
    duration: 'permanent',
    effect: {
      type: 'damage',
      value: 1,
      condition: 'when playing rock',
    },
  },
  {
    id: 'paper_shield',
    name: 'Paper Shield',
    cost: 2,
    moveType: 'paper',
    chaosPoints: 1,
    duration: 3,
    effect: {
      type: 'defense',
      value: 1,
    },
  },
  {
    id: 'scissors_fury',
    name: 'Scissors Fury',
    cost: 4,
    moveType: 'scissors',
    chaosPoints: 2,
    duration: 'single',
    effect: {
      type: 'damage',
      value: 3,
      condition: 'when playing scissors',
    },
  },
  // Add more upgrades as needed...
]; 

plugins/upgrades/types and /utils exist as well