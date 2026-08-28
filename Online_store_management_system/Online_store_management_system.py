"""Система керування інтернет-магазином.

Використані патерни:
    Factory       - створення товарів (звичайний / цифровий / підписка)
    State         - стани замовлення та залежна від стану поведінка
    Strategy      - способи оплати та способи доставки
    Observer      - сповіщення (Email / SMS / Admin) з підпискою й відпискою
    Decorator     - додаткові послуги (знижка, промокод, пакування, страхування)
    Command       - черга команд + скасування останньої дії (undo)
    Singleton     - єдина система логування

Гроші скрізь рахуються у Decimal (без похибок float), статус замовлення —
через Enum, а команди звертаються тільки до публічного API замовлення.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


def money(value) -> Decimal:
    """Звести будь-яке число до грошового значення з двома знаками."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ----------------------------------------------------------------------
# 8. Логування - Singleton
# ----------------------------------------------------------------------
class Logger:
    """Єдиний на всю програму логер."""

    _instance: "Logger | None" = None

    def __new__(cls) -> "Logger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._records = []
        return cls._instance

    def log(self, message: str) -> None:
        self._records.append(message)
        print(f"[LOG] {message}")

    @property
    def records(self) -> list[str]:
        return list(self._records)

    def clear(self) -> None:
        """Очистити історію (зручно для тестів)."""
        self._records.clear()


# ----------------------------------------------------------------------
# 1. Товари - Factory
# ----------------------------------------------------------------------
class Product(ABC):
    def __init__(self, name: str, price) -> None:
        self.name = name
        self.price = money(price)

    @abstractmethod
    def info(self) -> str:
        ...

    def __str__(self) -> str:
        return f"{self.name} — {self.price:.2f} грн ({self.info()})"


class SimpleProduct(Product):
    def __init__(self, name: str, price, weight: float) -> None:
        super().__init__(name, price)
        self.weight = weight

    def info(self) -> str:
        return f"звичайний товар, вага {self.weight} кг"


class DigitalProduct(Product):
    def __init__(self, name: str, price, size_mb: float) -> None:
        super().__init__(name, price)
        self.size_mb = size_mb

    def info(self) -> str:
        return f"цифровий товар, {self.size_mb} МБ"


class SubscriptionProduct(Product):
    def __init__(self, name: str, price, months: int) -> None:
        super().__init__(name, price)
        self.months = months

    def info(self) -> str:
        return f"підписка на {self.months} міс."


class ProductFactory:
    """Фабрика товарів: новий тип додається реєстрацією, без зміни клієнтського коду."""

    _registry: dict[str, type[Product]] = {
        "simple": SimpleProduct,
        "digital": DigitalProduct,
        "subscription": SubscriptionProduct,
    }

    @classmethod
    def register(cls, kind: str, product_cls: type[Product]) -> None:
        cls._registry[kind] = product_cls

    @classmethod
    def create(cls, kind: str, **kwargs) -> Product:
        try:
            product_cls = cls._registry[kind]
        except KeyError:
            raise ValueError(f"Невідомий тип товару: {kind}") from None
        product = product_cls(**kwargs)
        Logger().log(f"Створено товар: {product.name}")
        return product


# ----------------------------------------------------------------------
# 3. Оплата - Strategy
# ----------------------------------------------------------------------
class PaymentMethod(ABC):
    name: str = "оплата"

    @abstractmethod
    def pay(self, amount: Decimal) -> bool:
        ...


class CardPayment(PaymentMethod):
    name = "Картка"

    def __init__(self, card_number: str) -> None:
        self.card_number = card_number

    def pay(self, amount: Decimal) -> bool:
        print(f"Оплата {amount:.2f} грн карткою **** {self.card_number[-4:]}")
        return True


class PayPalPayment(PaymentMethod):
    name = "PayPal"

    def __init__(self, email: str) -> None:
        self.email = email

    def pay(self, amount: Decimal) -> bool:
        print(f"Оплата {amount:.2f} грн через PayPal ({self.email})")
        return True


class CryptoPayment(PaymentMethod):
    name = "Криптовалюта"

    def __init__(self, wallet: str, currency: str = "BTC") -> None:
        self.wallet = wallet
        self.currency = currency

    def pay(self, amount: Decimal) -> bool:
        print(f"Оплата {amount:.2f} грн у {self.currency} на гаманець {self.wallet}")
        return True


# ----------------------------------------------------------------------
# 4. Доставка - Strategy
# ----------------------------------------------------------------------
class DeliveryMethod(ABC):
    name: str = "доставка"

    @abstractmethod
    def describe(self) -> str:
        ...


class CourierDelivery(DeliveryMethod):
    name = "Кур'єр"

    def __init__(self, address: str) -> None:
        self.address = address

    def describe(self) -> str:
        return f"кур'єр за адресою {self.address}"


class PostDelivery(DeliveryMethod):
    name = "Пошта"

    def __init__(self, office: str) -> None:
        self.office = office

    def describe(self) -> str:
        return f"пошта, відділення {self.office}"


class PickupDelivery(DeliveryMethod):
    name = "Самовивіз"

    def __init__(self, point: str) -> None:
        self.point = point

    def describe(self) -> str:
        return f"самовивіз з точки {self.point}"


# ----------------------------------------------------------------------
# 2. Статус замовлення - Enum
# ----------------------------------------------------------------------
class OrderStatus(Enum):
    NEW = "Нове"
    PROCESSING = "В обробці"
    SHIPPED = "Відправлено"
    DELIVERED = "Доставлено"
    CANCELLED = "Скасовано"


# ----------------------------------------------------------------------
# 5. Сповіщення - Observer
# ----------------------------------------------------------------------
@dataclass
class Event:
    kind: str            # "status" або "message"
    order: "Order"
    old: OrderStatus | None = None
    new: OrderStatus | None = None
    text: str = ""


class Observer(ABC):
    @abstractmethod
    def update(self, event: Event) -> None:
        ...


class Notifier(Observer):
    channel: str = "Notifier"

    @abstractmethod
    def status_text(self, event: Event) -> str:
        ...

    def update(self, event: Event) -> None:
        text = event.text if event.kind == "message" else self.status_text(event)
        print(f"{self.channel}: {text}")
        Logger().log(f"Надіслано {self.channel}")


class EmailNotifier(Notifier):
    channel = "Email"

    def __init__(self, email: str) -> None:
        self.email = email

    def status_text(self, event: Event) -> str:
        return "Вам надіслано повідомлення про зміну статусу."


class SmsNotifier(Notifier):
    channel = "SMS"

    def __init__(self, phone: str) -> None:
        self.phone = phone

    def status_text(self, event: Event) -> str:
        return "Статус вашого замовлення змінено."


class AdminNotifier(Notifier):
    channel = "Admin"

    def status_text(self, event: Event) -> str:
        old = event.old.value if event.old else "—"
        new = event.new.value if event.new else "—"
        return f"Замовлення №{event.order.number}: «{old}» → «{new}»."


class Publisher:
    """Джерело подій із можливістю підписки/відписки (Observer subject)."""

    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
            Logger().log(f"Підписано: {getattr(observer, 'channel', observer)}")

    def unsubscribe(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
            Logger().log(f"Відписано: {getattr(observer, 'channel', observer)}")

    def _emit(self, event: Event) -> None:
        for observer in list(self._observers):
            observer.update(event)


# ----------------------------------------------------------------------
# 6. Додаткові послуги - Decorator
# ----------------------------------------------------------------------
class PriceComponent(ABC):
    @abstractmethod
    def total(self) -> Decimal:
        ...

    @abstractmethod
    def describe(self) -> str:
        ...


class BasePrice(PriceComponent):
    def __init__(self, order: "Order") -> None:
        self._order = order

    def total(self) -> Decimal:
        return money(sum((item.price for item in self._order.items), Decimal("0")))

    def describe(self) -> str:
        return "товари"


class OrderExtra(PriceComponent):
    """Базовий декоратор: обгортає попередню ціну."""

    def __init__(self) -> None:
        self.component: PriceComponent | None = None


class Discount(OrderExtra):
    def __init__(self, percent: float) -> None:
        super().__init__()
        self.percent = percent

    def total(self) -> Decimal:
        factor = (Decimal("100") - Decimal(str(self.percent))) / Decimal("100")
        return money(self.component.total() * factor)

    def describe(self) -> str:
        return f"знижка {self.percent:g}%"


class PromoCode(OrderExtra):
    def __init__(self, code: str, amount) -> None:
        super().__init__()
        self.code = code
        self.amount = money(amount)

    def total(self) -> Decimal:
        return money(max(Decimal("0"), self.component.total() - self.amount))

    def describe(self) -> str:
        return f"промокод {self.code} (-{self.amount:.2f} грн)"


class GiftWrap(OrderExtra):
    def __init__(self, price=50.0) -> None:
        super().__init__()
        self.price = money(price)

    def total(self) -> Decimal:
        return money(self.component.total() + self.price)

    def describe(self) -> str:
        return f"подарункове пакування (+{self.price:.2f} грн)"


class Insurance(OrderExtra):
    """Страхування — фіксована плата (узгоджено з рештою послуг)."""

    def __init__(self, price=60.0) -> None:
        super().__init__()
        self.price = money(price)

    def total(self) -> Decimal:
        return money(self.component.total() + self.price)

    def describe(self) -> str:
        return f"страхування (+{self.price:.2f} грн)"


# ----------------------------------------------------------------------
# 2. Стани замовлення - State
# ----------------------------------------------------------------------
class OrderState(ABC):
    status: OrderStatus

    def pay(self, order: "Order") -> bool:
        return self._deny(order, "оплатити")

    def ship(self, order: "Order") -> bool:
        return self._deny(order, "відправити")

    def deliver(self, order: "Order") -> bool:
        return self._deny(order, "доставити")

    def cancel(self, order: "Order") -> bool:
        order.set_state(CancelledState())
        return True

    def _deny(self, order: "Order", action: str) -> bool:
        message = f"Неможливо {action} замовлення №{order.number}: стан «{self.status.value}»"
        print(message)
        Logger().log(message)
        return False


class NewState(OrderState):
    status = OrderStatus.NEW

    def pay(self, order: "Order") -> bool:
        if order.payment is None:
            return self._deny(order, "оплатити (спосіб оплати не обрано)")
        if not order.payment.pay(order.total()):
            return self._deny(order, "оплатити (платіж відхилено)")
        order.paid = True
        order.set_state(ProcessingState())
        return True


class ProcessingState(OrderState):
    status = OrderStatus.PROCESSING

    def ship(self, order: "Order") -> bool:
        order.set_state(ShippedState())
        return True


class ShippedState(OrderState):
    status = OrderStatus.SHIPPED

    def deliver(self, order: "Order") -> bool:
        order.set_state(DeliveredState())
        return True


class DeliveredState(OrderState):
    status = OrderStatus.DELIVERED

    def cancel(self, order: "Order") -> bool:
        return self._deny(order, "скасувати")


class CancelledState(OrderState):
    status = OrderStatus.CANCELLED

    def cancel(self, order: "Order") -> bool:
        return self._deny(order, "скасувати повторно")


# ----------------------------------------------------------------------
# Замовлення
# ----------------------------------------------------------------------
class Order(Publisher):
    def __init__(self, number: int, customer: str) -> None:
        super().__init__()
        self.number = number
        self.customer = customer
        self.items: list[Product] = []
        self.payment: PaymentMethod | None = None
        self.delivery: DeliveryMethod | None = None
        self.paid = False
        self._state: OrderState = NewState()
        self._price: PriceComponent = BasePrice(self)
        self._history: list["Command"] = []

    # --- товари й ціна ---
    def add_product(self, product: Product) -> None:
        self.items.append(product)
        Logger().log(f"До замовлення №{self.number} додано товар: {product.name}")

    def total(self) -> Decimal:
        return self._price.total()

    def add_extra(self, extra: OrderExtra) -> None:
        extra.component = self._price
        self._price = extra
        Logger().log(f"Додано послугу: {extra.describe()}")

    def remove_last_extra(self) -> OrderExtra | None:
        if not isinstance(self._price, OrderExtra):
            return None
        removed = self._price
        self._price = removed.component
        Logger().log(f"Видалено послугу: {removed.describe()}")
        return removed

    def price_report(self) -> str:
        chain: list[OrderExtra] = []
        node = self._price
        while isinstance(node, OrderExtra):
            chain.append(node)
            node = node.component
        chain.reverse()
        lines = [f"Замовлення: {node.total():.2f} грн"]
        for extra in chain:
            lines.append(f"+ {extra.describe()} → {extra.total():.2f} грн")
        lines.append(f"Фінальна ціна: {self.total():.2f} грн")
        return "\n".join(lines)

    # --- стратегії ---
    def set_payment(self, method: PaymentMethod) -> None:
        self.payment = method
        Logger().log(f"Обрано оплату: {method.name}")

    def set_delivery(self, method: DeliveryMethod) -> None:
        self.delivery = method
        Logger().log(f"Обрано доставку: {method.name} — {method.describe()}")

    # --- стани (публічний API, яким користуються команди) ---
    @property
    def status(self) -> OrderStatus:
        return self._state.status

    def current_state(self) -> OrderState:
        return self._state

    def set_state(self, state: OrderState) -> None:
        old, new = self._state.status, state.status
        self._state = state
        Logger().log(f"Статус змінено: {old.value} → {new.value}")
        print(f'Статус замовлення №{self.number} змінено:\n"{old.value}" → "{new.value}"')
        self._emit(Event(kind="status", order=self, old=old, new=new))

    def restore_state(self, state: OrderState) -> None:
        """Тихе повернення стану (використовується в undo)."""
        Logger().log(f"Відкат статусу: {self._state.status.value} → {state.status.value}")
        self._state = state

    def pay(self) -> bool:
        return self._state.pay(self)

    def ship(self) -> bool:
        return self._state.ship(self)

    def deliver(self) -> bool:
        return self._state.deliver(self)

    def cancel(self) -> bool:
        return self._state.cancel(self)

    # --- сповіщення ---
    def send_message(self, text: str) -> None:
        self._emit(Event(kind="message", order=self, text=text))

    # --- історія команд ---
    def remember(self, command: "Command") -> None:
        self._history.append(command)

    def undo(self) -> None:
        if not self._history:
            print("Немає дій для скасування")
            return
        command = self._history.pop()
        Logger().log(f"undo: {command.title}")
        command.undo()

    def __str__(self) -> str:
        return (f"Замовлення №{self.number} | {self.customer} | {self.status.value} | "
                f"{self.total():.2f} грн")


class Shop:
    def __init__(self, name: str, notifiers: list[Observer] | None = None) -> None:
        self.name = name
        self.orders: dict[int, Order] = {}
        self._counter = 151
        self._notifiers = list(notifiers or [])

    def next_number(self) -> int:
        self._counter += 1
        return self._counter

    def create_order(self, number: int, customer: str) -> Order:
        order = Order(number, customer)
        for notifier in self._notifiers:
            order.subscribe(notifier)
        self.orders[number] = order
        print(f"Замовлення №{number} створено.")
        Logger().log(f"Створено замовлення №{number}")
        Logger().log(f"Користувач: {customer}")
        return order


# ----------------------------------------------------------------------
# 7. Черга команд - Command (+ undo)
#
# Команди звертаються до замовлення через OrderRef — тримач посилання, який
# заповнює CreateOrderCommand. Це дозволяє додати всі команди в чергу ще до
# того, як замовлення фактично створене, без перевірок типу джерела.
# ----------------------------------------------------------------------
class OrderRef:
    """Спільне посилання на замовлення для команд у черзі."""

    def __init__(self, order: Order | None = None) -> None:
        self.order = order


class Command(ABC):
    title: str = "Команда"

    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


class CreateOrderCommand(Command):
    def __init__(self, shop: Shop, ref: OrderRef, customer: str,
                 products: list[Product], delivery: DeliveryMethod | None = None) -> None:
        self.shop = shop
        self.ref = ref
        self.customer = customer
        self.products = products
        self.delivery = delivery
        self.number = shop.next_number()
        self.title = f"Створення замовлення №{self.number}"

    def execute(self) -> None:
        order = self.shop.create_order(self.number, self.customer)
        for product in self.products:
            order.add_product(product)
        if self.delivery:
            order.set_delivery(self.delivery)
        self.ref.order = order
        order.remember(self)

    def undo(self) -> None:
        self.ref.order.cancel()


class PayOrderCommand(Command):
    def __init__(self, ref: OrderRef, method: PaymentMethod) -> None:
        self.ref = ref
        self.method = method
        self.title = "Оплата замовлення"
        self._prev_state: OrderState | None = None
        self._prev_method: PaymentMethod | None = None
        self._prev_paid = False

    def execute(self) -> None:
        order = self.ref.order
        self.title = f"Оплата замовлення №{order.number}"
        self._prev_state = order.current_state()
        self._prev_method = order.payment
        self._prev_paid = order.paid
        order.set_payment(self.method)
        if order.pay():
            order.remember(self)

    def undo(self) -> None:
        order = self.ref.order
        order.paid = self._prev_paid
        order.payment = self._prev_method
        order.restore_state(self._prev_state)
        print(f"Оплату замовлення №{order.number} скасовано (статус: {order.status.value})")


class ChangeDeliveryCommand(Command):
    def __init__(self, ref: OrderRef, method: DeliveryMethod) -> None:
        self.ref = ref
        self.method = method
        self.title = "Зміна способу доставки"
        self._prev: DeliveryMethod | None = None

    def execute(self) -> None:
        order = self.ref.order
        self._prev = order.delivery
        order.set_delivery(self.method)
        order.remember(self)

    def undo(self) -> None:
        order = self.ref.order
        if self._prev is None:
            order.delivery = None
            print("Спосіб доставки скинуто")
        else:
            order.set_delivery(self._prev)
            print(f"Повернуто попередній спосіб доставки: {self._prev.name}")


class AddExtraCommand(Command):
    def __init__(self, ref: OrderRef, extra: OrderExtra) -> None:
        self.ref = ref
        self.extra = extra
        self.title = f"Додавання послуги: {extra.describe()}"

    def execute(self) -> None:
        self.ref.order.add_extra(self.extra)
        self.ref.order.remember(self)

    def undo(self) -> None:
        removed = self.ref.order.remove_last_extra()
        if removed is not None:
            print(f"Видалено: {removed.describe()}. Ціна: {self.ref.order.total():.2f} грн")


class SendNotificationCommand(Command):
    def __init__(self, ref: OrderRef, text: str) -> None:
        self.ref = ref
        self.text = text
        self.title = "Надсилання повідомлення"

    def execute(self) -> None:
        # у історію undo не потрапляє: надіслане повідомлення не відкликається
        self.ref.order.send_message(self.text)

    def undo(self) -> None:
        print("Надіслане повідомлення скасувати неможливо")


class CancelOrderCommand(Command):
    def __init__(self, ref: OrderRef) -> None:
        self.ref = ref
        self.title = "Скасування замовлення"
        self._prev_state: OrderState | None = None

    def execute(self) -> None:
        order = self.ref.order
        self._prev_state = order.current_state()
        if order.cancel():
            order.remember(self)

    def undo(self) -> None:
        self.ref.order.restore_state(self._prev_state)
        print(f"Скасування відмінено, статус: {self.ref.order.status.value}")


class CommandQueue:
    """Черга команд: додаємо дії та виконуємо їх послідовно."""

    def __init__(self) -> None:
        self._commands: list[Command] = []

    def add(self, command: Command) -> Command:
        self._commands.append(command)
        return command

    def run(self) -> None:
        for index, command in enumerate(self._commands, start=1):
            print(f"\n[{index}] {command.title}")
            command.execute()
        self._commands.clear()


# ----------------------------------------------------------------------
# Демонстрація
# ----------------------------------------------------------------------
def header(text: str) -> None:
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def main() -> None:
    log = Logger()

    header("1. Товари (Factory)")
    products = [
        ProductFactory.create("simple", name="Ковбаса крафтова", price=600, weight=1.2),
        ProductFactory.create("digital", name="Курс з рецептур", price=300, size_mb=850),
        ProductFactory.create("subscription", name="Клуб дегустацій", price=100, months=3),
    ]
    for product in products:
        print(product)

    header("2. Черга команд (Command)")
    email = EmailNotifier("oleksandr@mail.com")
    sms = SmsNotifier("+380671234567")
    admin = AdminNotifier()
    shop = Shop("Добра ковбаска", notifiers=[email, sms, admin])

    ref = OrderRef()
    queue = CommandQueue()
    queue.add(CreateOrderCommand(shop, ref, "Oleksandr", products, PostDelivery("№12")))
    queue.add(PayOrderCommand(ref, PayPalPayment("oleksandr@mail.com")))
    queue.add(ChangeDeliveryCommand(ref, CourierDelivery("вул. Хрещатик, 1")))
    queue.add(SendNotificationCommand(ref, "Ваше замовлення передано кур'єру."))
    queue.run()

    order = ref.order

    header("3. Додаткові послуги (Decorator)")
    extras = CommandQueue()
    extras.add(AddExtraCommand(ref, Discount(10)))
    extras.add(AddExtraCommand(ref, PromoCode("SAUSAGE", 50)))
    extras.add(AddExtraCommand(ref, GiftWrap()))
    extras.add(AddExtraCommand(ref, Insurance()))
    extras.run()
    print()
    print(order.price_report())

    header("4. Скасування останніх дій (undo)")
    order.undo()   # прибирає страхування
    order.undo()   # прибирає подарункове пакування
    order.undo()   # прибирає промокод
    order.undo()   # прибирає знижку
    order.undo()   # повертає попередній спосіб доставки
    order.undo()   # скасовує оплату
    print()
    print(order.price_report())
    print(order)

    header("5. Стани замовлення (State)")
    order.set_payment(CardPayment("4441111122223333"))
    order.pay()
    order.unsubscribe(sms)
    order.ship()
    order.deliver()
    order.ship()      # доставлене замовлення відправити повторно не можна
    order.cancel()    # і скасувати теж

    header("6. Друге замовлення: самовивіз і скасування")
    ref2 = OrderRef()
    second = CommandQueue()
    second.add(CreateOrderCommand(
        shop, ref2, "Iryna",
        [ProductFactory.create("simple", name="Шинка", price=450, weight=0.8)],
        PickupDelivery("Магазин на Подолі"),
    ))
    second.add(PayOrderCommand(ref2, CryptoPayment("bc1q...x7", "BTC")))
    second.add(CancelOrderCommand(ref2))
    second.run()
    print()
    print(ref2.order)

    header("7. Логер - один об'єкт (Singleton)")
    print(f"Logger() is Logger(): {Logger() is log}")
    print(f"Усього записів у лозі: {len(log.records)}")


if __name__ == "__main__":
    main()
