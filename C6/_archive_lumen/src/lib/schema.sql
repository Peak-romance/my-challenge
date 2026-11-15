-- 聚光 Lumen 数据库架构 (SQLite)
-- 通过 node:sqlite 在应用启动时执行；seed 脚本复用同一份 DDL。

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT UNIQUE NOT NULL,
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  bio           TEXT DEFAULT '',
  avatar_color  TEXT DEFAULT '#fb8106',
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS posts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  summary      TEXT DEFAULT '',
  content      TEXT NOT NULL,
  cover_emoji  TEXT DEFAULT '✨',
  status       TEXT DEFAULT 'published',
  views        INTEGER DEFAULT 0,
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
  id   INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS post_tags (
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  tag_id  INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, tag_id)
);

CREATE TABLE IF NOT EXISTS comments (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id   INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
  content   TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS likes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS bookmarks (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS follows (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  followee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (follower_id, followee_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_author     ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_created    ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_post_tags_tag    ON post_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_comments_post    ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_likes_post       ON likes(post_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user   ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
