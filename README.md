
# Mini-CRM Lead Distributor

A FastAPI service to distribute leads from various sources (bots) to operators based on weighted competence and load limits.

## Tech Stack
- Python 3.11
- FastAPI
- SQLAlchemy (Async) + aiosqlite
- Docker

## Quick Start

### Using Docker
1. Build and run:
   ```bash
   docker-compose up --build
   ```
2. Access API documentation at `http://localhost:8000/docs`.

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run server:
   ```bash
   uvicorn src.main:app --reload
   ```

## Model Architecture

- **Operator**: Has `is_active` status and `max_load` limit.
- **Source**: Represents a channel (e.g., "Bot A").
- **SourceOperatorLink**: Many-to-Many link storing the `weight` (competence) of an operator for a specific source.
- **Lead**: Unique client identified by a string (e.g., email/phone).
- **Case**: An interaction event linking Lead, Source, and assigned Operator.

## Distribution Algorithm

The logic resides in `src/crm/service.py`: `_select_operator`.

1. **Identification**: Logic looks up `Lead` by identifier; creates one if missing.
2. **Filtering**:
   - Fetch all operators configured for the incoming `Source`.
   - Filter out `is_active=False`.
   - Filter out operators where `Current Open Cases >= Max Load`.
3. **Selection**:
   - Uses **Weighted Random Selection** (`random.choices`) based on the weights defined in the Source-Operator configuration.
   - This ensures that over time, the distribution matches the target percentages (e.g., weights 10 and 30 result in a ~25%/75% split).
4. **Fallback**:
   - If no operators are available (all inactive or full), the Case is created with `operator_id=None`.

## API Usage Example

1. **Create Operator**: `POST /operators` `{"name": "Alice", "max_load": 5}`
2. **Create Source**: `POST /sources` `{"name": "TelegramBot"}`
3. **Configure**: `PUT /sources/1/distribution`
   ```json
   {
     "operators": [{"operator_id": 1, "weight": 50}]
   }
   ```
4. **Register Lead**: `POST /cases`
   ```json
   {
     "lead_identifier": "user@example.com",
     "source_id": 1,
     "message": "Hello"
   }
   ```