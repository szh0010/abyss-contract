"""
深渊树洞 · 反诈机器人冷启动种子帖。

用法（项目根目录）：
    cd backend
    python -m app.seed_forum            # 默认幂等：已存在的机器人帖跳过
    python -m app.seed_forum --reset    # 先清空所有 user_id IS NULL 的机器人帖再灌

约定：
- 机器人帖的 user_id 一律为 NULL（与真实用户无关），author_name 直存。
- 幂等键：author_name + content 前 60 字。
"""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete

from app.database import AsyncSessionLocal, init_db
from app.models.post import Post


SEED_POSTS = [
    {
        "author": "反诈卫士-壹号",
        "content": (
            "【典型案例】昨天接到\"京东金融客服\"电话，"
            "声称我大学时绑定的校园贷未注销会影响征信。"
            "记住三句话：① 任何要求转账验资的都是骗子；② 96110 是反诈热线；"
            "③ 立刻挂断、不要按对方说的下载任何 APP。"
        ),
    },
    {
        "author": "城南派出所-小李警官",
        "content": (
            "再三提醒大家：警察办案绝不会通过电话/网络要求你转账或屏幕共享。"
            "凡是要求你下载\"安全防护 APP\" 的，100% 是诈骗。"
            "遇到此类情况请直接挂断后到最近派出所核实。"
        ),
    },
    {
        "author": "防骗老阿姨",
        "content": (
            "刚帮邻居老王守住了 3 万块。对方自称是他\"在新加坡的儿子\"，"
            "微信换头像、说手机进水、要应急。我让老王打视频——对面立刻挂了。"
            "亲属求助务必视频核实，这一招屡试不爽。"
        ),
    },
    {
        "author": "校园反诈联络员",
        "content": (
            "高校新生季又到了：刷单返现、注销贷款、冒充辅导员收费——"
            "这三类骗局占新生案件 80% 以上。请大家把这条转发给身边的同学，"
            "记住一句话：只要让你转账，先打 96110。"
        ),
    },
]


async def _exists(session, author: str, head: str) -> bool:
    """以 (author, content[:60]) 作为幂等键判断是否已经写过。"""
    res = await session.execute(
        select(Post.id)
        .where(Post.user_id.is_(None))
        .where(Post.author_name == author)
        .where(Post.content.like(f"{head}%"))
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


async def _reset_bot_posts(session) -> int:
    res = await session.execute(delete(Post).where(Post.user_id.is_(None)))
    return res.rowcount or 0


async def seed(reset: bool = False) -> None:
    await init_db()  # 防止首次运行时表还没建
    async with AsyncSessionLocal() as session:
        if reset:
            n = await _reset_bot_posts(session)
            print(f"[seed] cleared {n} existing bot posts")

        # 给种子帖错开时间，让前端排序更自然
        now = datetime.now(timezone.utc)
        added = 0
        for i, item in enumerate(SEED_POSTS):
            head = item["content"][:60]
            if await _exists(session, item["author"], head):
                print(f"[seed] skip (exists): {item['author']}")
                continue
            session.add(Post(
                user_id=None,
                author_name=item["author"],
                content=item["content"],
                created_at=now - timedelta(hours=i * 6 + 1),
            ))
            added += 1
            print(f"[seed] add: {item['author']}")

        await session.commit()
        print(f"[seed] done. added {added} bot posts.")


def main() -> None:
    parser = argparse.ArgumentParser(description="深渊树洞冷启动种子")
    parser.add_argument(
        "--reset", action="store_true",
        help="先清掉所有机器人帖（user_id IS NULL）再灌",
    )
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset))


if __name__ == "__main__":
    main()
