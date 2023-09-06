/**
 * Модификация функии fetch с поддержкой таймаута.
 * Отправляет HTTP-запросы в бэкенд
 * https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
 * @param url - URL запроса
 * @param opts - параметры запроса
 * @param timeout - таймаут в миллисекундах
 * @returns {Promise<Response>} Результат запроса (или выбрасывает исключение при ощибках запроса)
 */
export const fetchWithTimeout = async (url, opts = {}, timeout = 5000) => {
    const signal = AbortSignal.timeout(timeout);

    const _fetchPromise = fetch(url, {
        ...opts,
        signal,
    });

    return await _fetchPromise;
};
