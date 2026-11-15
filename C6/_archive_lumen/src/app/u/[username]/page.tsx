import { notFound } from "next/navigation";
import { getProfileData, publicUser } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";
import { Avatar } from "@/components/Avatar";
import { PostCard } from "@/components/PostCard";
import { FollowButton } from "@/components/FollowButton";

export const dynamic = "force-dynamic";

export default async function ProfilePage({
  params,
}: {
  params: { username: string };
}) {
  const viewer = await getSessionUser();
  const data = getProfileData(params.username, viewer?.id ?? 0);
  if (!data) notFound();

  const isSelf = !!viewer && viewer.id === data.user.id;
  const pubUser = publicUser(data.user);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-2xl border border-ink-100 p-6 shadow-soft">
        <div className="flex items-start gap-4">
          <Avatar user={pubUser} size={64} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-ink-900 truncate">
                {data.user.display_name}
              </h1>
              {!isSelf && (
                <FollowButton
                  username={data.user.username}
                  initialFollowing={data.is_following}
                />
              )}
            </div>
            <p className="text-sm text-ink-400">@{data.user.username}</p>
            {data.user.bio && (
              <p className="mt-2 text-sm text-ink-700 whitespace-pre-wrap">{data.user.bio}</p>
            )}
            <div className="mt-3 flex gap-5 text-sm text-ink-500">
              <span>
                <b className="text-ink-900">{data.post_count}</b> 文章
              </span>
              <span>
                <b className="text-ink-900">{data.follower_count}</b> 粉丝
              </span>
              <span>
                <b className="text-ink-900">{data.following_count}</b> 关注
              </span>
            </div>
          </div>
        </div>
      </div>

      <h2 className="text-base font-bold text-ink-900 mt-6 mb-3">TA 的文章</h2>
      {data.posts.length === 0 ? (
        <p className="text-sm text-ink-400">还没有发布文章。</p>
      ) : (
        <div className="space-y-4">
          {data.posts.map((p) => (
            <PostCard key={p.id} post={p} showAuthor={false} />
          ))}
        </div>
      )}
    </div>
  );
}
