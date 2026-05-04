from abc import ABC, abstractmethod

class Notification(ABC):
    @abstractmethod
    def send_notification(self, message: str) -> None:
        pass

class EmailNotification(Notification):
    def send_notification(self, message: str) -> None:
        print(f"Sending email notification: {message}")

class SMSNotification(Notification):
    def send_notification(self, message: str) -> None:
        print(f"Sending SMS notification: {message}")

class NotificationFactory(ABC):
    @abstractmethod
    def create_notification(self) -> Notification:
        pass

class EmailNotificationFactory(NotificationFactory):
    def create_notification(self) -> Notification:
        return EmailNotification()

class SMSNotificationFactory(NotificationFactory):
    def create_notification(self) -> Notification:
        return SMSNotification()

def send_notification(factory: NotificationFactory, message: str) -> None:
    notification = factory.create_notification()
    notification.send_notification(message)


# Example usage
if __name__ == "__main__":
    send_notification(EmailNotificationFactory(), "Your ticket has been created.")
    send_notification(SMSNotificationFactory(), "Your ticket has been updated.")