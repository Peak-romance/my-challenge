import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { existsSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";

// ---------------------------------------------------------------------------
// Database singleton
// ---------------------------------------------------------------------------
// node:sqlite is bundled with Node >= 22.5, so we get a real relational store
// with zero external dependencies and zero native compilation. The connection
// is a process-wide singleton (survives Next.js hot-reload via globalThis).

const SCHEMA_PATH = join(process.cwd(), "src", "lib", "schema.sql");

function resolveDbPath(): string {
  const fromEnv = process.env.DATABASE_PATH;
  const candidates: string[] = [];
  if (fromEnv) candidates.push(fromEnv);
  candidates.push(join(process.cwd(), "data", "lumen.db"));
  candidates.push(join(tmpdir(), "lumen.db"));

  for (const p of candidates) {
    try {
      const dir = dirname(p);
      if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
      return p;
    } catch {
      // try next candidate (e.g. read-only filesystem)
      continue;
    }
  }
  return candidates[candidates.length - 1];
}

type DbGlobal = { __lumenDb?: DatabaseSync };
const g = globalThis as unknown as DbGlobal;

export function getDb(): DatabaseSync {
  if (g.__lumenDb) return g.__lumenDb;

  const dbPath = resolveDbPath();
  const db = new DatabaseSync(dbPath);
  db.exec("PRAGMA journal_mode = WAL;");
  db.exec("PRAGMA foreign_keys = ON;");

  const schema = readFileSync(SCHEMA_PATH, "utf8");
  db.exec(schema);

  g.__lumenDb = db;
  return db;
}
