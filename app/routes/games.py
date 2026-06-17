
import time
import random




from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Header
from app.models import GameRound
from app.schemas import RoundResultCreate

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import User
from app.models import Bet

from app.schemas import BetCreate

from app.auth import decode_access_token

from app.models import SystemConfig

import time

router = APIRouter(
    prefix="/game",
    tags=["Game"]
)

ROUND_DURATION = 60

GAME_START_TIMESTAMP = 1750000000


def get_current_user(
    authorization: str,
    db: Session
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    payload = decode_access_token(
        token
    )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.id == payload["user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user

def settle_previous_round(
    db: Session
):

    elapsed = (
        int(time.time())
        - GAME_START_TIMESTAMP
    )

    current_period = (
        elapsed // ROUND_DURATION
    )

    previous_period = str(
        current_period - 1
    )

    existing_round = db.query(
        GameRound
    ).filter(
        GameRound.period == previous_period
    ).first()

    if existing_round:
        return

    bets = db.query(Bet).filter(
        Bet.period == previous_period
    ).all()

    colors = [
        "GREEN",
        "RED",
        "YELLOW",
        "VIOLET"
    ]

    counts = {
        "GREEN": 0,
        "RED": 0,
        "YELLOW": 0,
        "VIOLET": 0
    }

    for bet in bets:
        counts[bet.color] += 1

    active_counts = {
    color: count
    for color, count in counts.items()
    if count > 0
    }
    config = db.query(
        SystemConfig
    ).first()

    game_mode = (
        config.game_mode
        if config
        else "BET_COUNT"
    )

    if game_mode == "RANDOM":

        result = random.choice(
            colors
        )

    else:

        if not active_counts:

            result = random.choice(
                colors
            )

        else:

            lowest_count = min(
                active_counts.values()
            )

            possible_winners = [
                color
                for color, count
                in active_counts.items()
                if count == lowest_count
            ]

            result = random.choice(
                possible_winners
            )

       

    round_result = GameRound(
        period=previous_period,
        result=result,
        game_mode="BET_COUNT"
    )

    db.add(round_result)

    for bet in bets:

        if bet.color == result:

            bet.status = "WON"

            payout = (
                bet.amount * 2
            )

            bet.payout = payout

            user = db.query(User).filter(
                User.id == bet.user_id
            ).first()

            if user:
                user.balance += payout

        else:

            bet.status = "LOST"
            bet.payout = 0

    db.commit()
@router.get("/current")
def get_current_round(
    db: Session = Depends(get_db)
):

    settle_previous_round(db)

    elapsed = (
        int(time.time())
        - GAME_START_TIMESTAMP
    )

    period = (
        elapsed // ROUND_DURATION
    )

    remaining = (
        ROUND_DURATION
        - (elapsed % ROUND_DURATION)
    )

    return {
        "period": str(period),
        "remaining": remaining
    }


@router.get("/history")
def get_history(
    db: Session = Depends(get_db)
):
    rounds = (
        db.query(GameRound)
        .order_by(GameRound.id.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "period": r.period,
            "result": r.result
        }
        for r in rounds
    ]


@router.post("/bet")
def place_bet(
    bet_data: BetCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )
    existing_bet = db.query(Bet).filter(
        Bet.user_id == user.id,
        Bet.period == bet_data.period
    ).first()

    if existing_bet:
        raise HTTPException(
            status_code=400,
            detail="You already placed a bet for this round"
        )

    if user.balance < bet_data.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance"
        )

    user.balance -= bet_data.amount

    bet = Bet(
        user_id=user.id,
        period=bet_data.period,
        color=bet_data.color,
        amount=bet_data.amount,
    )

    db.add(bet)

    db.commit()

    db.refresh(user)

    return {
        "message": "Bet placed successfully",
        "balance": user.balance,
        "username": user.username
    }
@router.post("/round-result")
def create_round_result(
    data: RoundResultCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(GameRound).filter(
        GameRound.period == data.period
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Round already exists"
        )

    round_result = GameRound(
        period=data.period,
        result=data.result
    )

    db.add(round_result)

    bets = db.query(Bet).filter(
        Bet.period == data.period
    ).all()

    for bet in bets:

        if bet.color == data.result:

            bet.status = "WON"

            payout = bet.amount * 2

            bet.payout = payout

            user = db.query(User).filter(
                User.id == bet.user_id
            ).first()

            if user:
                user.balance += payout

        else:

            bet.status = "LOST"
            bet.payout = 0

    db.commit()

    db.refresh(round_result)

    return {
        "message": "Round saved and settled",
        "period": round_result.period,
        "result": round_result.result,
        "bets_processed": len(bets)
    }
@router.get("/my-bets")
def get_my_bets(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )

    bets = (
        db.query(Bet)
        .filter(
            Bet.user_id == user.id
        )
        .order_by(Bet.id.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "period": bet.period,
            "color": bet.color,
            "amount": bet.amount,
            "status": bet.status
        }
        for bet in bets
    ]
@router.delete("/cancel-bet/{period}")
def cancel_bet(
    period: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    print("AUTH:", authorization)

    user = get_current_user(
        authorization,
        db
    )

    bet = db.query(Bet).filter(
        Bet.user_id == user.id,
        Bet.period == period
    ).first()

    if not bet:
        raise HTTPException(
            status_code=404,
            detail="Bet not found"
        )

    if bet.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Bet already settled"
        )

    elapsed = (
        int(time.time())
        - GAME_START_TIMESTAMP
    )

    remaining = (
        ROUND_DURATION
        - (elapsed % ROUND_DURATION)
    )

    if remaining <= 5:
        raise HTTPException(
            status_code=400,
            detail="Bet is locked"
        )

    user.balance += bet.amount

    db.delete(bet)

    db.commit()

    return {
        "message": "Bet cancelled",
        "balance": user.balance
    }

@router.get("/mode")
def get_mode(
    db: Session = Depends(get_db)
):

    config = db.query(
        SystemConfig
    ).first()

    if not config:

        config = SystemConfig(
            game_mode="BET_COUNT"
        )

        db.add(config)
        db.commit()

    return {
        "mode": config.game_mode
    }
@router.post("/mode")
def set_mode(
    mode: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )

    if user.username != "Thanveer":
        raise HTTPException(
            status_code=403,
            detail="Admin only"
        )

    config = db.query(
        SystemConfig
    ).first()

    if not config:

        config = SystemConfig()

        db.add(config)

    config.game_mode = mode

    db.commit()

    return {
        "message": "Mode updated",
        "mode": mode
    }