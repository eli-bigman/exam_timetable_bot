""" firebase helper functions"""
import logging
import re
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage

# log config
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

try:
    # Read service account credentials securely using a context manager
    cred = credentials.Certificate("./serviceAccount.json")

    # Initialize Firebase app
    firebase_admin.initialize_app(
        cred, {"storageBucket": "ug-exams-bot.appspot.com"})

    db = firestore.client()

except FileNotFoundError as e:
    logger.error(f"🔥Error loading service account credentials: {e}")
    raise

except Exception as e:
    logger.exception(f"🔥Unexpected error initializing Firebase app: {e}")
    raise


def get_course_code(user_id: str, course) -> str:

    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        doc_ref = db.collection('users').document(str(user_id))
        doc = doc_ref.get()

        if doc.exists:
            course_code = doc.get(
                f'{sanitized_course}.course_code')
            return course_code
        else:
            return None

    except Exception as e:
        logger.exception(
            f"🔥Error retrieving course code for user ID {user_id}: {e}")
        return None


def set_course_code(user_id: str, course, course_code: str) -> None:

    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        db.collection('users').document(str(user_id)).update(
            {f'{sanitized_course}.course_code': course_code})

    except Exception as e:
        logger.exception(
            f"🔥Error setting course code for user ID {user_id}: {e}")


def get_saved_exams_details(user_id: str) -> dict | None:

    doc_ref = db.collection('users').document(user_id)
    try:
        doc = doc_ref.get()
        if doc.exists:
            exams_details = doc.to_dict()
            return exams_details
        else:
            return None
    except Exception as e:
        logger.error(f'🔥Error getting exams details: {e}')
        return None


def save_exams_details(user_id: str, course: str, course_info: dict) -> None:
    """Save all exams details to firebase"""
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            sanitized_course = re.sub(r'\W+', '_', course)
            doc_ref.update({
                sanitized_course: course_info
            })
        else:
            sanitized_course = re.sub(r'\W+', '_', course)
            doc_ref.create(document_data={
                sanitized_course: course_info
            })

    except Exception as e:
        logger.exception(
            f"🔥Error saving exams details for {user_id}: {e}"
        )
        return None


def get_exams_venue(user_id: str) -> str:
    """Retrive all exams venue for all courses"""
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            all_exams_venue = doc.get('All_Exams_Venue')
            return all_exams_venue
        else:
            return None
    except Exception as e:
        logger.exception(
            f"🔥Error retrieving exams venue for user ID {user_id}: {e}")
        return None


def set_exact_venue(user_id: str, course, exact_venue: str) -> None:

    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        db.collection('users').document(str(user_id)).update(
            {f'{sanitized_course}.Exact_Exams_Venue': exact_venue})

    except Exception as e:
        logger.exception(
            f"🔥Error setting exact exams venue for user ID {user_id}: {e}")


def get_exact_venue(user_id: str, course):
    """
    Format course name to be used as dict key
    Get exact venue value
    """
    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            exact_exams_venue = doc.get(
                f'{sanitized_course}.Exact_Exams_Venue')
            return exact_exams_venue
        else:
            return None
    except KeyError as e:
        logger.exception(
            f"🔥Error getting exact exams venue for user ID {user_id}: {e}")
        return None


def set_no_id_venues(user_id: str, course: str, no_id_venue: list):
    """
    Save venues without ID attached
    """
    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        # doc_ref = db.collection('users').document(user_id)
        # doc = doc_ref.get()
        if len(no_id_venue) > 0:

            db.collection('users').document(user_id).update({
                f'{sanitized_course}.No_ID_Venues': no_id_venue
            })
        else:
            db.collection('users').document(user_id).update({
                f'{sanitized_course}.No_ID_Venues': None
            })

    except Exception as e:
        logger.error(f"🔥Error Set no id venue failed -{str(e)}")


def get_no_id_venues(user_id: str, course: str) -> list | None:
    """
    Retrive venues without IDs attached
    """
    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            no_id_venue = doc.get(f'{sanitized_course}.No_ID_Venues')
            return no_id_venue
        else:
            return None

    except Exception as e:
        logger.error(f"🔥Error getting no_id_venues \n {e}")


def delete_exams_details(user_id: str) -> None:
    """
    Delete saved exams details from user document
    """

    try:
        exams_details = get_saved_exams_details(user_id)
        if not exams_details:
            return None

        courses = exams_details.keys()
        for course in courses:
            db.collection('users').document(user_id).update({
                f"{course}": firestore.DELETE_FIELD
            })

    except Exception as e:
        logger.error(f"🔥An error occurred while deleting exams details: {e}")
        return None


def upload_screenshot_to_firebase(local_file_path: str, remote_file_name: str) -> str:
    """
    Upload screenschot to firebase 
    delete local copy and
    return a public url of the screenshot
    """

    try:
        # Upload to firebase storage
        bucket = storage.bucket()
        blob = bucket.blob(f"screenshots/{remote_file_name}")
        blob.upload_from_filename(local_file_path)

        # return public url
        blob.make_public()
        public_url = blob.public_url

        # delete local copy
        os.remove(local_file_path)

        return public_url

    except Exception as e:
        logger.exception(f'🔥Upload screenshot failed : {str(e)} ')


def upload_calendar_to_firebase(local_file_path: str, remote_file_name: str) -> str:
    """
    Upload calender.ics file to firebase 
    delete local copy and
    return a public url of the screenshot
    """

    try:
        # Upload to firebase storage
        bucket = storage.bucket()
        blob = bucket.blob(f"calendars/{remote_file_name}")
        blob.upload_from_filename(local_file_path)

        # return public url
        blob.make_public()
        public_url = blob.public_url

        # delete local copy
        os.remove(local_file_path)

        return public_url

    except Exception as e:
        logger.exception(f'🔥Upload calendar failed : {str(e)}')


def delete_from_firebase_storage(remote_file_name: str):
    """
    Delete screenshot from firebase
    """

    try:
        bucket = storage.bucket()
        blob = bucket.blob(f"screenshots/{remote_file_name}")
        blob.delete()

    except Exception as e:
        logger.error(f"🔥Error deleting screenshot - {str(e)}")


if __name__ == "__main__":
    user_id = "271330483"
    # user_id = "123456789"
    # set_course_code(user_id, "UGBS303")
    # save_exams_details(user_id, "UGBS303 - COMPUTER APPLICATIONS IN MANAGEMENT", "01 March 2024",
    #                   "02:32 pm", "test")
    # set_exact_venue(
    #     user_id, "UGBS303_COMPUTER_APPLICATIONS_IN_MANAGEMENT", "UGCS LAB 3 MAIN")
    # get_exact_venue(user_id, "UGBS303 - COMPUTER APPLICATIONS IN MANAGEMENT")
    get_saved_exams_details(user_id)
    # get_exams_venue(user_id)
    # get_course_code(user_id)
    # delete_exams_details(
    #     user_id)
