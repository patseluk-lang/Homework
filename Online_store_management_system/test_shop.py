"""Тести для системи керування інтернет-магазином (Online_store_management_system.py).

Перевіряють головне: коректність фабрики, guard-и станів, точність цін у
Decimal, роботу декораторів, undo та Observer.
"""
from decimal import Decimal

import pytest

from Online_store_management_system import (
    AddExtraCommand, CardPayment, ChangeDeliveryCommand, CommandQueue,
    CourierDelivery, CreateOrderCommand, Discount, GiftWrap, Insurance, Logger,
    Order, OrderRef, OrderStatus, Observer, PayOrderCommand, PickupDelivery,
    PostDelivery, Product, ProductFactory, PromoCode, Shop, SimpleProduct,
)


def make_order(number: int = 1, price=1000) -> Order:
    order = Order(number, "Тест")
    order.add_product(SimpleProduct("Товар", price, weight=1.0))
    return order


# --- Factory --------------------------------------------------------------
def test_factory_creates_all_types():
    p1 = ProductFactory.create("simple", name="A", price=100, weight=1.0)
    p2 = ProductFactory.create("digital", name="B", price=100, size_mb=10)
    p3 = ProductFactory.create("subscription", name="C", price=100, months=6)
    assert p1.info().startswith("звичайний")
    assert p2.info().startswith("цифровий")
    assert p3.info().startswith("підписка")


def test_factory_unknown_type_raises():
    with pytest.raises(ValueError):
        ProductFactory.create("hologram", name="X", price=1)


def test_factory_register_new_type():
    class GiftCard(Product):
        def __init__(self, name, price, code):
            super().__init__(name, price)
            self.code = code

        def info(self) -> str:
            return "подарункова картка"

    ProductFactory.register("giftcard", GiftCard)
    p = ProductFactory.create("giftcard", name="GC", price=500, code="ABC")
    assert isinstance(p, GiftCard)
    assert p.info() == "подарункова картка"


def test_prices_are_decimal():
    p = ProductFactory.create("simple", name="A", price=99.9, weight=1.0)
    assert isinstance(p.price, Decimal)
    assert p.price == Decimal("99.90")


# --- Decorator (точність Decimal) -----------------------------------------
def test_decorator_chain_totals():
    order = make_order(price=1000)
    assert order.total() == Decimal("1000.00")
    order.add_extra(Discount(10))                    # 1000 -> 900
    assert order.total() == Decimal("900.00")
    order.add_extra(PromoCode("SALE", 50))           # 900 -> 850
    assert order.total() == Decimal("850.00")
    order.add_extra(GiftWrap(50))                    # 850 -> 900
    assert order.total() == Decimal("900.00")
    order.add_extra(Insurance(60))                   # 900 -> 960
    assert order.total() == Decimal("960.00")


def test_promo_never_below_zero():
    order = make_order(price=30)
    order.add_extra(PromoCode("BIG", 100))
    assert order.total() == Decimal("0.00")


# --- State (поведінка залежить від стану) ---------------------------------
def test_pay_requires_method():
    order = make_order()
    assert order.pay() is False
    assert order.status is OrderStatus.NEW


def test_pay_advances_to_processing():
    order = make_order()
    order.set_payment(CardPayment("4441111122223333"))
    assert order.pay() is True
    assert order.status is OrderStatus.PROCESSING
    assert order.paid is True


def test_full_lifecycle():
    order = make_order()
    order.set_payment(CardPayment("1111222233334444"))
    order.pay()                       # New -> Processing
    assert order.ship() is True       # Processing -> Shipped
    assert order.status is OrderStatus.SHIPPED
    assert order.deliver() is True    # Shipped -> Delivered
    assert order.status is OrderStatus.DELIVERED


def test_delivered_cannot_be_shipped_again():
    order = make_order()
    order.set_payment(CardPayment("1111222233334444"))
    order.pay()
    order.ship()
    order.deliver()
    assert order.ship() is False                 # доставлене не відправляється
    assert order.status is OrderStatus.DELIVERED


def test_delivered_cannot_be_cancelled():
    order = make_order()
    order.set_payment(CardPayment("1111222233334444"))
    order.pay()
    order.ship()
    order.deliver()
    assert order.cancel() is False
    assert order.status is OrderStatus.DELIVERED


def test_new_order_can_be_cancelled():
    order = make_order()
    assert order.cancel() is True
    assert order.status is OrderStatus.CANCELLED


# --- Undo -----------------------------------------------------------------
def test_undo_removes_last_extra():
    order = make_order(price=1000)
    ref = OrderRef(order)
    AddExtraCommand(ref, Discount(10)).execute()
    AddExtraCommand(ref, Insurance(60)).execute()
    assert order.total() == Decimal("960.00")
    order.undo()                                  # прибирає страхування
    assert order.total() == Decimal("900.00")
    order.undo()                                  # прибирає знижку
    assert order.total() == Decimal("1000.00")


def test_undo_change_delivery_restores_previous():
    order = make_order()
    order.set_delivery(PostDelivery("№1"))
    ref = OrderRef(order)
    ChangeDeliveryCommand(ref, CourierDelivery("вул. Тестова, 1")).execute()
    assert order.delivery.name == "Кур'єр"
    order.undo()
    assert order.delivery.name == "Пошта"


def test_undo_pay_restores_state_and_method():
    order = make_order()
    ref = OrderRef(order)
    PayOrderCommand(ref, CardPayment("4441111122223333")).execute()
    assert order.status is OrderStatus.PROCESSING
    order.undo()
    assert order.status is OrderStatus.NEW
    assert order.payment is None
    assert order.paid is False


def test_undo_on_empty_history_is_safe(capsys):
    order = make_order()
    order.undo()  # не повинно кидати виняток
    assert "Немає дій" in capsys.readouterr().out


# --- Observer -------------------------------------------------------------
class _Recorder(Observer):
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


def test_observer_subscribe_and_unsubscribe():
    order = make_order()
    rec = _Recorder()
    order.subscribe(rec)
    order.set_payment(CardPayment("1111222233334444"))
    order.pay()                          # зміна статусу -> подія
    assert len(rec.events) == 1
    assert rec.events[0].new is OrderStatus.PROCESSING

    order.unsubscribe(rec)
    order.ship()                         # ще одна зміна статусу, але вже без підписки
    assert len(rec.events) == 1


# --- Command queue --------------------------------------------------------
def test_command_queue_runs_sequentially():
    shop = Shop("Тест-магазин")
    ref = OrderRef()
    queue = CommandQueue()
    queue.add(CreateOrderCommand(shop, ref, "Oleksandr",
                                 [SimpleProduct("Товар", 500, 1.0)]))
    queue.add(PayOrderCommand(ref, CardPayment("4441111122223333")))
    queue.run()
    assert ref.order is not None
    assert ref.order.status is OrderStatus.PROCESSING
    assert ref.order.number in shop.orders


def test_shop_numbering_starts_at_152():
    shop = Shop("Тест")
    assert shop.next_number() == 152
    assert shop.next_number() == 153


# --- Singleton ------------------------------------------------------------
def test_logger_is_singleton():
    assert Logger() is Logger()
