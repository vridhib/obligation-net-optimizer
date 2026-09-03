import pandas as pd
from decimal import Decimal
from django.db.models import Sum, Count, Q
from obligations.models import Obligation, NettingWindow, SettlementAttempt
from api.serializers import ObligationSerializer, NetPositionSerializer


def format_decimal(value) -> str:
    return str(Decimal(value or 0).quantize(Decimal("0.01")))


def normalize_obligations_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ensure required columns
    required = {'payer', 'payee', 'amount', 'timestamp'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Normalize timestamps to UTC-aware datetimes
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='raise')
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    else:
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

    if "currency" not in df.columns:
        df["currency"] = "USD"
    if "status" not in df.columns:
        df["status"] = Obligation.Status.PENDING

    return df


def create_obligations_from_records(records: list[dict]) -> dict:
    created, errors = [], []
    for record in records:
        serializer = ObligationSerializer(data=record)
        if serializer.is_valid():
            serializer.save()
            created.append(serializer.data)
        else:
            errors.append(serializer.errors)
    return {
            "created_count": len(created),
            "errors_count": len(errors),
            "created": created,
            "errors": errors
    }


def create_obligations_from_csv(file) -> dict:
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")

    df = normalize_obligations_df(df)
    records = df.to_dict(orient='records')
    return create_obligations_from_records(records)


def get_net_positions_for_window(window_param: str = "latest") -> dict:
    if window_param == "latest":
        window = NettingWindow.objects.order_by("-end_time").first()
    else:
        try:
            window_id = int(window_param)
            window = NettingWindow.objects.get(window_id=window_id)
        except (ValueError, NettingWindow.DoesNotExist):
            return None

    if not window:
        return {"window_id": None, "positions": []}

    positions = window.net_positions.all().order_by("participant")
    data = NetPositionSerializer(positions, many=True).data
    return {
        "window_id": window.window_id,
        "start_time": window.start_time,
        "end_time": window.end_time,
        "positions": data,
    }


def get_netting_summary() -> dict:
    windows = NettingWindow.objects.all()
    if not windows:
        return {
            "total_windows": 0,
            "gross_obligation_count": 0,
            "net_obligation_count": 0,
            "gross_volume": "0",
            "net_volume": "0",
            "liquidity_saved": "0",
            "settled_attempts": 0,
            "failed_attempts": 0,
        }

    totals = windows.aggregate(
        total_windows=Count("window_id"),
        total_gross_count=Sum("gross_obligation_count"),
        total_net_count=Sum("net_obligation_count"),
        total_gross_volume=Sum("gross_volume"),
        total_net_volume=Sum("net_volume"),
        total_liquidity_saved=Sum("liquidity_saved"),
    )

    attempts = SettlementAttempt.objects.filter(window__in=windows).aggregate(
        settled=Count("pk", filter=Q(status="settled")),
        failed=Count("pk", filter=Q(status="failed")),
    )

    return {
        "total_windows": totals["total_windows"],
        "gross_obligation_count": totals["total_gross_count"] or 0,
        "net_obligation_count": totals["total_net_count"] or 0,
        "gross_volume": format_decimal(totals["total_gross_volume"]),
        "net_volume": format_decimal(totals["total_net_volume"]),
        "liquidity_saved": format_decimal(totals["total_liquidity_saved"]),
        "settled_attempts": attempts["settled"],
        "failed_attempts": attempts["failed"],
    }


def get_graph_for_window(window_id: int, view: str) -> dict:
    window = NettingWindow.objects.get(window_id=window_id)

    if view == "gross":
        return _build_gross_graph(window)
    elif view == "net":
        return _build_net_graph(window)
    else:
        raise ValueError("view must be 'gross' or 'net'")


def _build_gross_graph(window):
    edges_data = (
        Obligation.objects
        .filter(netting_window=window)
        .values("payer", "payee")
        .annotate(total=Sum("amount"))
        .order_by("payer", "payee")
    )

    edges = []
    participants = set()
    for i, e in enumerate(edges_data):
        participants.add(e["payer"])
        participants.add(e["payee"])
        edges.append({
            "id": f"g_{i}",
            "source": e["payer"],
            "target": e["payee"],
            "amount": format_decimal(e["total"]),
        })

    nodes = [
        {"id": p, "label": p, "net_amount": None}
        for p in sorted(participants)
    ]

    return {
        "window_id": window.window_id,
        "view": "gross",
        "nodes": nodes,
        "edges": edges,
    }


def _build_net_graph(window):
    attempts = window.settlement_attempts.all().order_by("payer", "payee")
    edges = [
        {
            "id": f"n_{i}",
            "source": a.payer,
            "target": a.payee,
            "amount": format_decimal(a.amount),
        }
        for i, a in enumerate(attempts)
    ]

    net_positions = window.net_positions.all().order_by("participant")
    nodes = [
        {
            "id": np.participant,
            "label": np.participant,
            "net_amount": format_decimal(np.net_amount),
        }
        for np in net_positions
    ]

    return {
        "window_id": window.window_id,
        "view": "net",
        "nodes": nodes,
        "edges": edges,
    }