router = APIRouter()


@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code)


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.list_rooms()


@router.post("/rooms/{room_id}/tokens")
def generate_token(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    ip_address: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address)


@router.post("/rooms/{room_id}/recording")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


@router.post("/rooms/{room_id}/end")
def end_room(
    room_id: str,
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


@router.get("/rooms/{room_id}")
def get_room_details(room_id: str, db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)
