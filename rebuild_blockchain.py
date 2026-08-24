from backend.database import SessionLocal
from backend.models import User, BlockchainBlock
from backend.main import calculate_block_hash

db = SessionLocal()

try:
    users = db.query(User).all()

    for user in users:
        blocks = (
            db.query(BlockchainBlock)
            .filter(BlockchainBlock.user_id == user.id)
            .order_by(BlockchainBlock.block_number.asc())
            .all()
        )

        previous_hash = "0"

        for index, block in enumerate(blocks, start=1):
            # Normalize block numbering in case it was affected by old data.
            block.block_number = index

            # Preserve the existing date, energy, and bill values.
            date = block.date.date()
            energy = round(float(block.energy_kwh), 2)
            bill = round(float(block.bill), 2)

            block.energy_kwh = energy
            block.bill = bill
            block.previous_hash = previous_hash

            block.current_hash = calculate_block_hash(
                block_number=index,
                date=date,
                energy=energy,
                bill=bill,
                previous_hash=previous_hash
            )

            previous_hash = block.current_hash

        print(
            f"{user.username}: rebuilt {len(blocks)} blockchain blocks"
        )

    db.commit()
    print("Blockchain migration completed successfully.")

finally:
    db.close()
