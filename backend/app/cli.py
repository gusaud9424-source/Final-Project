import click

from . import db
from .models import Course, PointLedger, Reward, TaskProgress, User, XpLedger


def register_cli(app):
    @app.cli.command("show-progress")
    @click.option("--email", required=True, help="대상 사용자 이메일")
    @click.option("--course", "slug", required=True, help="과목 slug (예: xss-dom)")
    def show_progress(email, slug):
        """점검용(읽기 전용): 사용자·과목의 미션 완료 기록, 레벨 통과 기록, 보상 생성·수령 시각 출력"""
        user = User.query.filter_by(email=email).first()
        course = Course.query.filter_by(slug=slug).first()
        if not user or not course:
            raise click.ClickException("사용자 또는 과목을 찾을 수 없습니다.")
        click.echo(f"[task_progress] {email} / {slug}")
        for row in TaskProgress.query.filter_by(user_id=user.id, course_id=course.id).order_by(TaskProgress.completed_at):
            click.echo(f"  {row.task_key:<18} 완료 {row.completed_at}")
        click.echo("[rewards]")
        for row in Reward.query.filter(Reward.user_id == user.id, Reward.ref.like(f"%:{slug}%")).order_by(Reward.id):
            click.echo(f"  {row.source:<20} {row.ref:<35} {row.type:<5} {row.amount:>4} 생성 {row.created_at} 수령 {row.claimed_at}")

    @app.cli.command("reset-rewards")
    @click.option("--email", required=True, help="대상 사용자 이메일")
    @click.option("--course", "slug", required=True, help="과목 slug (예: command-injection)")
    @click.option("--yes", is_flag=True, help="지정 시 실제 삭제. 없으면 삭제 대상만 출력")
    def reset_rewards(email, slug, yes):
        """시연용: 특정 사용자·과목의 실습/미션 보상 기록과 방어 퀴즈 완료 기록 초기화"""
        user = User.query.filter_by(email=email).first()
        if not user:
            raise click.ClickException(f"사용자를 찾을 수 없습니다: {email}")
        course = Course.query.filter_by(slug=slug).first()
        if not course:
            raise click.ClickException(f"과목을 찾을 수 없습니다: {slug}")

        refs = [f"practice:{slug}", f"mission:{slug}"]
        queries = {
            "xp_ledger": XpLedger.query.filter(XpLedger.user_id == user.id, XpLedger.ref.in_(refs)),
            "point_ledger": PointLedger.query.filter(PointLedger.user_id == user.id, PointLedger.ref.in_(refs)),
            "rewards": Reward.query.filter(Reward.user_id == user.id, Reward.ref.in_(refs)),
            # 방어 퀴즈 완료 기록이 남으면 퀴즈 폼이 숨겨져 미션 재시연 불가
            "task_progress(defense)": TaskProgress.query.filter_by(
                user_id=user.id, course_id=course.id, task_key="defense"
            ),
        }

        for name, query in queries.items():
            click.echo(f"{name}: {query.count()}건")

        if not yes:
            click.echo("미리보기만 수행했습니다. 실제 삭제하려면 --yes 를 붙이세요.")
            return

        for query in queries.values():
            query.delete(synchronize_session=False)
        db.session.commit()
        click.echo("초기화 완료.")

    @app.cli.command("set-password")
    @click.option("--username", required=True, help="대상 계정 아이디 (예: admin)")
    @click.password_option("--password", prompt="새 비밀번호", confirmation_prompt="새 비밀번호 확인",
                           help="생략 시 화면에 표시되지 않는 입력창으로 묻는다")
    def set_password(username, password):
        """서버 관리자용: 계정 비밀번호 재설정 (관리자 비밀번호 분실 시 복구)"""
        import bcrypt

        user = User.query.filter_by(username=username).first()
        if not user:
            raise click.ClickException(f"존재하지 않는 계정입니다: {username}")
        if len(password) < 8:
            raise click.ClickException("비밀번호는 8자 이상이어야 합니다.")

        user.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        db.session.commit()
        click.echo(f"[{user.role}] {username} 비밀번호를 변경했습니다.")

    @app.cli.command("dedupe-rewards")
    @click.option("--yes", is_flag=True, help="지정 시 실제 삭제. 없으면 삭제 대상만 출력")
    def dedupe_rewards(yes):
        """과목 보상을 과목별 1종(경험치/포인트)으로 정리.

        구버전에서 실습 보상이 경험치+포인트 2종으로 지급된 데이터를
        과목별 정식 1종만 남기고 나머지(Reward·원장)를 삭제한다.
        """
        from .rewards import COURSE_REWARD_TYPE, LEDGER_MODELS

        sources = ("concept", "practice", "mission")
        removed_rewards = 0
        removed_ledger = 0

        for slug, canonical in COURSE_REWARD_TYPE.items():
            non_canonical = [t for t in ("xp", "point") if t != canonical]
            for source in sources:
                ref = f"{source}:{slug}"
                # 보물상자(Reward) 비정식 종류 제거
                q = Reward.query.filter(
                    Reward.ref == ref, Reward.type.in_(non_canonical)
                )
                removed_rewards += q.count()
                if yes:
                    q.delete(synchronize_session=False)
                # 원장 비정식 종류 제거
                for t in non_canonical:
                    model = LEDGER_MODELS[t]
                    lq = model.query.filter_by(source=source, ref=ref)
                    removed_ledger += lq.count()
                    if yes:
                        lq.delete(synchronize_session=False)

        if yes:
            db.session.commit()
            click.echo(f"정리 완료: 보상 {removed_rewards}행, 원장 {removed_ledger}행 삭제.")
        else:
            click.echo(f"[미리보기] 삭제 대상 — 보상 {removed_rewards}행, 원장 {removed_ledger}행. 실제 삭제는 --yes.")
