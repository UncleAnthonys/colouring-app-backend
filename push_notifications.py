"""
Push notification helper for Little Lines backend.
Sends FCM notifications when generation tasks complete.
Requires firebase_admin to already be initialised (firebase_utils.init_firebase).
"""

import logging
from firebase_admin import messaging, firestore
from firebase_utils import init_firebase

logger = logging.getLogger(__name__)


def _get_fcm_token(user_id: str) -> str | None:
    """Look up a user's FCM token from Firestore."""
    init_firebase()
    db = firestore.client()
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        logger.warning(f"No Firestore doc for user {user_id}")
        return None
    return doc.to_dict().get("fcmToken")


def send_push(user_id: str, title: str, body: str, data: dict = None) -> bool:
    if not user_id:
        return False
    try:
        token = _get_fcm_token(user_id)
        if not token:
            logger.warning(f"No FCM token for user {user_id}")
            return False

        notification_data = {"click_action": "FLUTTER_NOTIFICATION_CLICK"}
        if data:
            for k, v in data.items():
                notification_data[k] = str(v)

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=notification_data,
            token=token,
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default", badge=1, mutable_content=True),
                ),
            ),
        )
        response = messaging.send(message)
        logger.info(f"Push sent to {user_id}: {response}")
        return True
    except messaging.UnregisteredError:
        logger.warning(f"Stale FCM token for {user_id}, clearing")
        try:
            init_firebase()
            db = firestore.client()
            db.collection("users").document(user_id).update({"fcmToken": firestore.DELETE_FIELD})
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(f"Push failed for {user_id}: {e}")
        return False
