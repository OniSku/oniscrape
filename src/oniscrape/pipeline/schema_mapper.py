from typing import Any, TypeVar

import jmespath
from pydantic import BaseModel, TypeAdapter

T = TypeVar("T", bound=BaseModel)


def map_state_to_model(
    state: dict[str, Any] | list[Any],
    query: str,
    model_cls: type[T],
    strict: bool = False,
    default: Any = None,
) -> list[T] | T | None:
    """Выполняет поиск по JMESPath-запросу в структуре состояния и валидирует результат в Pydantic v2 модель(и).

    Args:
        state: Исходный JSON-словарь или массив данных состояния.
        query: JMESPath-выражение (например, "props.pageProps.items[*].{id: id, name: title}").
        model_cls: Pydantic v2 класс схемы данных.
        strict: Если True, выбрасывает ValueError при пустом результате поиска.
        default: Значение по умолчанию, если ничего не найдено в non-strict режиме.

    Returns:
        Экземпляр модели T, список list[T], или default.
    """
    extracted = jmespath.search(query, state)

    # Проверка на пустой результат
    if extracted is None or (isinstance(extracted, list) and len(extracted) == 0):
        if strict:
            raise ValueError(f"JMESPath query '{query}' returned empty result in strict mode")

        # Если в запросе была проекция списка или default указан как список
        is_list_query = "[*" in query or query.endswith("]") or query.endswith("}")
        if default is None and is_list_query:
            return []
        return default

    # Если результат - список словарей
    if isinstance(extracted, list):
        adapter = TypeAdapter(list[model_cls])
        return adapter.validate_python(extracted)

    # Если результат - одиночный объект
    if isinstance(extracted, dict):
        return model_cls.model_validate(extracted)

    # Примитивное значение не мапится напрямую в модель
    if strict:
        raise ValueError(
            f"Expected dict or list from query '{query}', got {type(extracted).__name__}"
        )
    return default
