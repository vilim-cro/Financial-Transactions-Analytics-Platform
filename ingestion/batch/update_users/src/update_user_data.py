"""Script to randomly update user data in the all_users database."""
import logging
import random
import sys
from typing import List, Tuple

import psycopg2

from config import (
    CITIES,
    JOBS,
    LOG_FORMAT,
    LOG_LEVEL,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    UPDATABLE_FIELDS,
    UPDATE_PERCENTAGE,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def connect_postgres() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        logger.info(
            f"Connected to PostgreSQL database {POSTGRES_DB} at {POSTGRES_HOST}:{POSTGRES_PORT}"
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise


def get_user_count(conn: psycopg2.extensions.connection) -> int:
    """Get total number of users in the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        logger.info(f"Total users in database: {count}")
        return count


def get_random_users(
    conn: psycopg2.extensions.connection, count: int
) -> List[Tuple[str]]:
    """Get random user IDs from the database."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id FROM users ORDER BY RANDOM() LIMIT %s",
            (count,),
        )
        user_ids = cur.fetchall()
        logger.info(f"Selected {len(user_ids)} random users for update")
        return user_ids


def generate_random_value(field: str) -> str:
    """Generate a random value for the given field."""
    if field == "city":
        return random.choice(CITIES)
    elif field == "job":
        return random.choice(JOBS)
    elif field == "zip":
        return str(random.randint(10000, 99999))
    else:
        raise ValueError(f"Unknown field: {field}")


def update_users(
    conn: psycopg2.extensions.connection,
    user_ids: List[Tuple[str]],
    field: str,
) -> int:
    """Update the specified field for the given users with random values."""
    updated_count = 0
    
    with conn.cursor() as cur:
        for (user_id,) in user_ids:
            random_value = generate_random_value(field)
            try:
                cur.execute(
                    f"UPDATE users SET {field} = %s WHERE user_id = %s",
                    (random_value, user_id),
                )
                updated_count += 1
                logger.debug(
                    f"Updated user {user_id}: {field} = {random_value}"
                )
            except psycopg2.Error as e:
                logger.error(
                    f"Error updating user {user_id} field {field}: {e}"
                )
                continue
    
    conn.commit()
    logger.info(f"Successfully updated {updated_count} users")
    return updated_count


def main() -> None:
    """Main function to orchestrate the user data update."""
    logger.info("Starting user data update process")
    
    try:
        # Connect to database
        conn = connect_postgres()
        
        try:
            # Get total user count
            total_users = get_user_count(conn)
            
            if total_users == 0:
                logger.warning("No users found in database. Exiting.")
                return
            
            # Calculate number of users to update
            users_to_update = max(1, int(total_users * UPDATE_PERCENTAGE))
            logger.info(
                f"Will update {users_to_update} users ({UPDATE_PERCENTAGE * 100:.1f}% of total)"
            )
            
            # Select random users
            random_user_ids = get_random_users(conn, users_to_update)
            
            if not random_user_ids:
                logger.warning("No users selected for update. Exiting.")
                return
            
            # Randomly choose a field to update
            field_to_update = random.choice(UPDATABLE_FIELDS)
            logger.info(f"Selected field to update: {field_to_update}")
            
            # Update users
            updated_count = update_users(conn, random_user_ids, field_to_update)
            
            logger.info(
                f"Update process completed: {updated_count} users updated with new {field_to_update} values"
            )
            
        finally:
            conn.close()
            logger.info("Database connection closed")
            
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
