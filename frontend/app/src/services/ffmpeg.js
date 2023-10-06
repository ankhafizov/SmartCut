import { createFFmpeg, fetchFile } from '@ffmpeg/ffmpeg';
import {secsToTimeStr, timeout} from "../utils/utils.js";

const ffmpeg = createFFmpeg({log: false});

let ffmpegLoading = false;

/**
 * Загружате FFMpeg в бразуер
 */
export const ensureFfmpegLoaded = async() => {
    if (ffmpeg.isLoaded()) { return true;}
    if (ffmpegLoading) {
        if (!ffmpeg.isLoaded()) {
            await timeout(1000);
            return await ensureFfmpegLoaded();
        }
    }
    ffmpegLoading = true;
    await ffmpeg.load();
    return ffmpeg.isLoaded();
};

/**
 * Вырезает интервал из переданного видео-файла
 * @param videoFile Видео-файл
 * @param start Секунда начала интервала
 * @param end Секунда коца интервала
 * @returns {Promise<ArrayBuffer>} Видео-файл с интервалом
 */
export const cutVideo = async(videoFile, start, end) => {
    ffmpeg.FS('writeFile', "input.mp4", await fetchFile(videoFile));
    await ffmpeg.run('-ss', secsToTimeStr(start), '-to', secsToTimeStr(end), '-i', 'input.mp4', '-map', '0', '-c', 'copy', 'output.mp4');
    const data = ffmpeg.FS("readFile", "output.mp4")
    return data.buffer;
}
