/**
 * Генерирует UUID
 * @returns {string} uuid
 */
export const uuidv4 = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
        .replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0,
                v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
}

/**
 * Асинхронная версия функции setTimeout
 * @param ms Количество миллисекунд
 */
export const timeout = (ms) => {
    return new Promise(resolve => {
        setTimeout(() => {
            resolve();
        },ms)
    })
}

/**
 * Переводит секунды в строку времени (например 91 в '00:01:31')
 * @param secs Количество секунд
 * @returns {string} Строка времени
 */
export const secsToTimeStr = (secs) => {
    const hours = parseInt(secs / 3600)
    secs -= hours*3600;
    const mins = parseInt(secs/60);
    secs -= mins*60;
    secs = parseInt(secs);
    return (hours < 10 ? "0"+hours : hours)+":"+(mins<10 ? "0"+mins : mins)+":"+(secs<10 ? "0"+secs : secs);
}

/**
 * Переводит строку времени в секунды (например '00:01:31' в 91)
 * @param timeStr Строка времени
 * @returns {number} Количество секунд
 */
export const timeStrToSecs = (timeStr) => {
    const [hours,mins,secs] = timeStr.split(":");
    return parseInt(hours)*3600+parseInt(mins)*60+parseInt(secs);
}
