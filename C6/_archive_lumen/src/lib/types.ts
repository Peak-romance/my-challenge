export interface User {
  id: number;
  username: string;
  email: string;
  display_name: string;
  bio: string;
  avatar_color: string;
  created_at: string;
}

export interface PostRow {
  id: number;
  author_id: number;
  title: string;
  summary: string;
  content: string;
  cover_emoji: string;
  status: string;
  views: number;
  created_at: string;
  updated_at: string;
}

export type PublicUser = Omit<User, "email">;

export interface PostWithMeta extends PostRow {
  author: PublicUser;
  tags: string[];
  like_count: number;
  comment_count: number;
  bookmark_count: number;
  liked_by_viewer: boolean;
  bookmarked_by_viewer: boolean;
}

export interface CommentWithUser {
  id: number;
  post_id: number;
  user_id: number;
  parent_id: number | null;
  content: string;
  created_at: string;
  user: PublicUser;
}

export interface TagCount {
  name: string;
  count: number;
}

export interface ProfileData {
  user: User;
  posts: PostWithMeta[];
  follower_count: number;
  following_count: number;
  post_count: number;
  is_following: boolean;
}
