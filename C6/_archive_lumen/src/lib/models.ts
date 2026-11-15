import { getDb } from "./db";
import type {
  User,
  PostRow,
  PostWithMeta,
  CommentWithUser,
  TagCount,
  ProfileData,
} from "./types";

/** Strip the private email field before sending a user object to clients. */
export function publicUser(u: User, includeEmail = false) {
  const { email, ...rest } = u;
  return includeEmail ? u : rest;
}

// ===========================================================================
// Users
// ===========================================================================
export function getUserById(id: number): User | null {
  const db = getDb();
  const row = db
    .prepare(
      `SELECT id, username, email, display_name, bio, avatar_color, created_at
       FROM users WHERE id = ?`
    )
    .get(id) as User | undefined;
  return row ?? null;
}

export function getUserByUsername(username: string): User | null {
  const db = getDb();
  const row = db
    .prepare(
      `SELECT id, username, email, display_name, bio, avatar_color, created_at
       FROM users WHERE username = ?`
    )
    .get(username) as User | undefined;
  return row ?? null;
}

export function getUserByEmail(email: string): User | null {
  const db = getDb();
  const row = db
    .prepare(
      `SELECT id, username, email, display_name, bio, avatar_color, created_at
       FROM users WHERE email = ?`
    )
    .get(email) as User | undefined;
  return row ?? null;
}

/** Used only during login to verify the password; returns the credential fields. */
export function getUserCredential(
  identifier: string
): { id: number; username: string; password_hash: string } | null {
  const db = getDb();
  const row = db
    .prepare(
      `SELECT id, username, password_hash FROM users WHERE email = ? OR username = ?`
    )
    .get(identifier, identifier) as
    | { id: number; username: string; password_hash: string }
    | undefined;
  return row ?? null;
}

export function createUser(data: {
  username: string;
  email: string;
  passwordHash: string;
  displayName: string;
  avatarColor: string;
}): User {
  const db = getDb();
  const info = db
    .prepare(
      `INSERT INTO users (username, email, password_hash, display_name, avatar_color)
       VALUES (?, ?, ?, ?, ?)`
    )
    .run(data.username, data.email, data.passwordHash, data.displayName, data.avatarColor);
  return getUserById(Number(info.lastInsertRowid))!;
}

export function updateUser(
  id: number,
  data: { display_name?: string; bio?: string; avatar_color?: string }
): User | null {
  const db = getDb();
  const sets: string[] = [];
  const params: unknown[] = [];
  if (data.display_name !== undefined) {
    sets.push("display_name = ?");
    params.push(data.display_name);
  }
  if (data.bio !== undefined) {
    sets.push("bio = ?");
    params.push(data.bio);
  }
  if (data.avatar_color !== undefined) {
    sets.push("avatar_color = ?");
    params.push(data.avatar_color);
  }
  if (sets.length === 0) return getUserById(id);
  params.push(id);
  db.prepare(`UPDATE users SET ${sets.join(", ")} WHERE id = ?`).run(...params);
  return getUserById(id);
}

// ===========================================================================
// Tags
// ===========================================================================
export function ensureTag(name: string): number {
  const db = getDb();
  const clean = name.trim().toLowerCase();
  if (!clean) return 0;
  db.prepare(`INSERT OR IGNORE INTO tags (name) VALUES (?)`).run(clean);
  const row = db.prepare(`SELECT id FROM tags WHERE name = ?`).get(clean) as
    | { id: number }
    | undefined;
  return row?.id ?? 0;
}

export function getTagsForPost(postId: number): string[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT t.name FROM tags t
       JOIN post_tags pt ON pt.tag_id = t.id
       WHERE pt.post_id = ? ORDER BY t.name`
    )
    .all(postId) as { name: string }[];
  return rows.map((r) => r.name);
}

export function getAllTags(): TagCount[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT t.name AS name, COUNT(pt.post_id) AS count
       FROM tags t LEFT JOIN post_tags pt ON pt.tag_id = t.id
       GROUP BY t.id ORDER BY count DESC, t.name LIMIT 30`
    )
    .all() as TagCount[];
  return rows;
}

function setPostTags(postId: number, tagNames: string[]): void {
  const db = getDb();
  db.prepare(`DELETE FROM post_tags WHERE post_id = ?`).run(postId);
  const seen = new Set<string>();
  for (const raw of tagNames) {
    const name = raw.trim().toLowerCase();
    if (!name || seen.has(name)) continue;
    if (name.length > 24) continue;
    seen.add(name);
    const tagId = ensureTag(name);
    if (tagId) db.prepare(`INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)`).run(postId, tagId);
  }
}

// ===========================================================================
// Posts
// ===========================================================================
export function createPost(data: {
  authorId: number;
  title: string;
  summary: string;
  content: string;
  coverEmoji: string;
  tags: string[];
}): PostRow {
  const db = getDb();
  const info = db
    .prepare(
      `INSERT INTO posts (author_id, title, summary, content, cover_emoji)
       VALUES (?, ?, ?, ?, ?)`
    )
    .run(
      data.authorId,
      data.title,
      data.summary,
      data.content,
      data.coverEmoji || "✨"
    );
  const postId = Number(info.lastInsertRowid);
  setPostTags(postId, data.tags);
  return getPostById(postId, data.authorId)!;
}

export function updatePost(
  id: number,
  data: {
    title?: string;
    summary?: string;
    content?: string;
    coverEmoji?: string;
    tags?: string[];
  }
): PostRow | null {
  const db = getDb();
  const sets: string[] = [];
  const params: unknown[] = [];
  if (data.title !== undefined) {
    sets.push("title = ?");
    params.push(data.title);
  }
  if (data.summary !== undefined) {
    sets.push("summary = ?");
    params.push(data.summary);
  }
  if (data.content !== undefined) {
    sets.push("content = ?");
    params.push(data.content);
  }
  if (data.coverEmoji !== undefined) {
    sets.push("cover_emoji = ?");
    params.push(data.coverEmoji);
  }
  if (sets.length) {
    sets.push("updated_at = datetime('now')");
    params.push(id);
    db.prepare(`UPDATE posts SET ${sets.join(", ")} WHERE id = ?`).run(...params);
  }
  if (data.tags !== undefined) setPostTags(id, data.tags);
  return getPostById(id, 0);
}

export function deletePost(id: number): void {
  const db = getDb();
  db.prepare(`DELETE FROM posts WHERE id = ?`).run(id);
}

export function incrementViews(id: number): void {
  const db = getDb();
  db.prepare(`UPDATE posts SET views = views + 1 WHERE id = ?`).run(id);
}

function hydratePost(r: any): PostWithMeta {
  const {
    like_count,
    comment_count,
    bookmark_count,
    liked_by_viewer,
    bookmarked_by_viewer,
    author_id,
    ...rest
  } = r;
  return {
    ...rest,
    author: publicUser(getUserById(author_id)!),
    tags: getTagsForPost(r.id),
    like_count: Number(like_count || 0),
    comment_count: Number(comment_count || 0),
    bookmark_count: Number(bookmark_count || 0),
    liked_by_viewer: Number(liked_by_viewer || 0) > 0,
    bookmarked_by_viewer: Number(bookmarked_by_viewer || 0) > 0,
  };
}

const POST_SELECT = `
  SELECT p.*,
    (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
    (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count,
    (SELECT COUNT(*) FROM bookmarks b WHERE b.post_id = p.id) AS bookmark_count,
    (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id AND l.user_id = ?) AS liked_by_viewer,
    (SELECT COUNT(*) FROM bookmarks b WHERE b.post_id = p.id AND b.user_id = ?) AS bookmarked_by_viewer
  FROM posts p
`;

export function getPostById(id: number, viewerId = 0): PostWithMeta | null {
  const db = getDb();
  const row = db.prepare(`${POST_SELECT} WHERE p.id = ?`).get(viewerId, viewerId, id) as
    | any
    | undefined;
  if (!row) return null;
  return hydratePost(row);
}

export interface ListPostsOpts {
  viewerId?: number;
  filter?: "latest" | "hot" | "following";
  tag?: string;
  authorId?: number;
  q?: string;
  limit?: number;
  offset?: number;
}

export function listPosts(opts: ListPostsOpts = {}): PostWithMeta[] {
  const db = getDb();
  const viewerId = opts.viewerId ?? 0;
  const where: string[] = ["p.status = 'published'"];
  const params: unknown[] = [viewerId, viewerId];

  if (opts.tag) {
    where.push(
      `p.id IN (SELECT pt.post_id FROM post_tags pt JOIN tags t ON t.id = pt.tag_id WHERE t.name = ?)`
    );
    params.push(opts.tag);
  }
  if (opts.authorId) {
    where.push(`p.author_id = ?`);
    params.push(opts.authorId);
  }
  if (opts.q) {
    const q = `%${opts.q}%`;
    where.push(`(p.title LIKE ? OR p.content LIKE ? OR p.summary LIKE ?)`);
    params.push(q, q, q);
  }
  if (opts.filter === "following" && viewerId) {
    where.push(
      `p.author_id IN (SELECT followee_id FROM follows WHERE follower_id = ?)`
    );
    params.push(viewerId);
  }

  const orderBy =
    opts.filter === "hot"
      ? "ORDER BY (like_count * 3 + comment_count * 2) DESC, p.created_at DESC"
      : "ORDER BY p.created_at DESC";

  params.push(opts.limit ?? 20, opts.offset ?? 0);
  const rows = db
    .prepare(`${POST_SELECT} WHERE ${where.join(" AND ")} ${orderBy} LIMIT ? OFFSET ?`)
    .all(...params) as any[];
  return rows.map(hydratePost);
}

export function getRelatedPosts(postId: number, tags: string[], limit = 3): PostWithMeta[] {
  if (!tags.length) return [];
  const db = getDb();
  const placeholders = tags.map(() => "?").join(", ");
  const params: unknown[] = [0, 0, postId];
  tags.forEach((t) => params.push(t));
  params.push(limit);
  const rows = db
    .prepare(
      `${POST_SELECT}
       WHERE p.status = 'published' AND p.id != ?
         AND p.id IN (SELECT pt.post_id FROM post_tags pt JOIN tags t ON t.id = pt.tag_id WHERE t.name IN (${placeholders}))
       ORDER BY (like_count * 2 + comment_count) DESC
       LIMIT ?`
    )
    .all(...params) as any[];
  return rows.map(hydratePost);
}

// ===========================================================================
// Comments
// ===========================================================================
export function addComment(data: {
  postId: number;
  userId: number;
  content: string;
  parentId?: number | null;
}): CommentWithUser {
  const db = getDb();
  const info = db
    .prepare(
      `INSERT INTO comments (post_id, user_id, parent_id, content) VALUES (?, ?, ?, ?)`
    )
    .run(data.postId, data.userId, data.parentId ?? null, data.content);
  return getCommentById(Number(info.lastInsertRowid))!;
}

export function getCommentById(id: number): CommentWithUser | null {
  const db = getDb();
  const row = db
    .prepare(
      `SELECT c.*, u.username, u.display_name, u.avatar_color, u.bio, u.email, u.created_at AS u_created
       FROM comments c JOIN users u ON u.id = c.user_id WHERE c.id = ?`
    )
    .get(id) as any;
  if (!row) return null;
  return shapeComment(row);
}

function shapeComment(row: any): CommentWithUser {
  const { username, display_name, avatar_color, bio, u_created, ...rest } = row;
  return {
    ...rest,
    user: publicUser({
      id: rest.user_id,
      username,
      email: "",
      display_name,
      bio: bio ?? "",
      avatar_color: avatar_color ?? "#fb8106",
      created_at: u_created,
    }),
  };
}

export function listComments(postId: number): CommentWithUser[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT c.*, u.username, u.display_name, u.avatar_color, u.bio, u.email, u.created_at AS u_created
       FROM comments c JOIN users u ON u.id = c.user_id
       WHERE c.post_id = ? ORDER BY c.created_at ASC`
    )
    .all(postId) as any[];
  return rows.map(shapeComment);
}

export function deleteComment(id: number, userId: number): boolean {
  const db = getDb();
  const c = db.prepare(`SELECT * FROM comments WHERE id = ?`).get(id) as any;
  if (!c) return false;
  if (c.user_id !== userId) {
    const post = db.prepare(`SELECT author_id FROM posts WHERE id = ?`).get(c.post_id) as any;
    if (!post || post.author_id !== userId) return false;
  }
  db.prepare(`DELETE FROM comments WHERE id = ?`).run(id);
  return true;
}

// ===========================================================================
// Likes
// ===========================================================================
export function toggleLike(postId: number, userId: number): { liked: boolean; count: number } {
  const db = getDb();
  const existing = db
    .prepare(`SELECT id FROM likes WHERE post_id = ? AND user_id = ?`)
    .get(postId, userId);
  if (existing) {
    db.prepare(`DELETE FROM likes WHERE post_id = ? AND user_id = ?`).run(postId, userId);
  } else {
    db.prepare(`INSERT INTO likes (post_id, user_id) VALUES (?, ?)`).run(postId, userId);
  }
  const count = (db.prepare(`SELECT COUNT(*) AS c FROM likes WHERE post_id = ?`).get(postId) as any)
    .c;
  return { liked: !existing, count: Number(count) };
}

// ===========================================================================
// Bookmarks
// ===========================================================================
export function toggleBookmark(
  postId: number,
  userId: number
): { bookmarked: boolean; count: number } {
  const db = getDb();
  const existing = db
    .prepare(`SELECT id FROM bookmarks WHERE post_id = ? AND user_id = ?`)
    .get(postId, userId);
  if (existing) {
    db.prepare(`DELETE FROM bookmarks WHERE post_id = ? AND user_id = ?`).run(postId, userId);
  } else {
    db.prepare(`INSERT INTO bookmarks (post_id, user_id) VALUES (?, ?)`).run(postId, userId);
  }
  const count = (
    db.prepare(`SELECT COUNT(*) AS c FROM bookmarks WHERE post_id = ?`).get(postId) as any
  ).c;
  return { bookmarked: !existing, count: Number(count) };
}

export function listBookmarks(userId: number): PostWithMeta[] {
  const db = getDb();
  const rows = db
    .prepare(`${POST_SELECT} WHERE p.id IN (SELECT post_id FROM bookmarks WHERE user_id = ?) ORDER BY p.created_at DESC`)
    .all(userId, userId, userId) as any[];
  return rows.map(hydratePost);
}

// ===========================================================================
// Follows
// ===========================================================================
export function toggleFollow(followerId: number, followeeId: number): { following: boolean } {
  if (followerId === followeeId) return { following: false };
  const db = getDb();
  const existing = db
    .prepare(`SELECT id FROM follows WHERE follower_id = ? AND followee_id = ?`)
    .get(followerId, followeeId);
  if (existing) {
    db.prepare(`DELETE FROM follows WHERE follower_id = ? AND followee_id = ?`).run(
      followerId,
      followeeId
    );
    return { following: false };
  }
  db.prepare(`INSERT INTO follows (follower_id, followee_id) VALUES (?, ?)`).run(
    followerId,
    followeeId
  );
  return { following: true };
}

export function isFollowing(followerId: number, followeeId: number): boolean {
  const db = getDb();
  const row = db
    .prepare(`SELECT id FROM follows WHERE follower_id = ? AND followee_id = ?`)
    .get(followerId, followeeId);
  return !!row;
}

export function getFollowCounts(userId: number): { followers: number; following: number } {
  const db = getDb();
  const followers = (
    db.prepare(`SELECT COUNT(*) AS c FROM follows WHERE followee_id = ?`).get(userId) as any
  ).c;
  const following = (
    db.prepare(`SELECT COUNT(*) AS c FROM follows WHERE follower_id = ?`).get(userId) as any
  ).c;
  return { followers: Number(followers), following: Number(following) };
}

// ===========================================================================
// Profile
// ===========================================================================
export function getProfileData(username: string, viewerId = 0): ProfileData | null {
  const user = getUserByUsername(username);
  if (!user) return null;
  const posts = listPosts({ authorId: user.id, viewerId, limit: 50 });
  const counts = getFollowCounts(user.id);
  const isFollowing = viewerId ? isFollowing(viewerId, user.id) : false;
  return {
    user,
    posts,
    follower_count: counts.followers,
    following_count: counts.following,
    post_count: posts.length,
    is_following: isFollowing,
  };
}
