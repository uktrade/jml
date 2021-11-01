from core.utils.sre_messages import (
    FailedToSendSREAlertMessage,
    FailedToSendSRECompleteMessage,
    send_sre_alert_message,
    send_sre_complete_message,
)

try:
    alert_response = send_sre_alert_message(
        first_name="John",
        last_name="Smith",
    )
except FailedToSendSREAlertMessage:
    print("Failed to send SRE alert message")
else:
    try:
        send_sre_complete_message(thread_ts=alert_response.data["ts"])
    except FailedToSendSRECompleteMessage:
        print("Failed to send SRE complete message")
