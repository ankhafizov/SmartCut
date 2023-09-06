import {useEffect} from "react";
import {Button, TimePicker} from "antd";
import {CloseOutlined, DownloadOutlined} from "@ant-design/icons";
import dayjs from "dayjs";
import {secsToTimeStr, timeStrToSecs} from "../utils/utils.js";
import {cutVideo, ensureFfmpegLoaded} from "../services/ffmpeg.js";

/**
 * Таблица видео-интервалов
 */
export default function ResultsTable(
    {videoFileName, videoSrc, intervals, setIntervals, selectedInterval,setSelectedInterval,changeVideoPositions}) {

    const video = document.getElementById("inputVideo");

    useEffect(() => {
        loadFfmpeg().then();
    },[])

    const render = () => {
        return (
            <>
                <table id="intervalsTable">
                    <tbody>
                    <tr>
                        <th>Начало</th>
                        <th>Конец</th>
                        <th>Длина</th>
                        <th>Действия</th>
                    </tr>
                    {intervals.map((interval,index) => renderInterval(interval, index))}
                    </tbody>
                </table>
                <div style={{display:intervals.length ? "" : "none"}} className="intervalsTableFooter">
                    <Button type="primary" icon={<DownloadOutlined/>} onClick={()=>downloadAllIntervals()}>
                        Скачать все
                    </Button>
                </div>
            </>
        )
    }

    const renderInterval = (interval, index) => {
        return (
            <tr key={"interval_"+index}>
                <td onClick={()=>selectInterval(index)}
                    className={index === selectedInterval ? "selected" : ""}>
                    <TimePicker value={dayjs(secsToTimeStr(interval.start), 'HH:mm:ss')} size="small"
                                onChange={(time,strTime) => {
                                    onTimeChange(index,strTime,'start')
                                }}
                                onSelect = {() => onTimeSelect(index,'start')}
                                changeOnBlur={true} popupStyle={{display:'none'}}
                    />

                </td>
                <td onClick={()=>selectInterval(index)}
                    className={index === selectedInterval ? "selected" : ""}>
                    <TimePicker value={dayjs(secsToTimeStr(interval.stop), 'HH:mm:ss')} size="small"
                                onChange={(time,strTime) => {
                                    onTimeChange(index,strTime,'stop')
                                }}
                                onSelect = {() => onTimeSelect(index,'stop')}
                                changeOnBlur={true} popupStyle={{display:'none'}}
                    />
                </td>
                <td onClick={()=>selectInterval(index)}
                    className={index === selectedInterval ? "selected" : ""}>
                    {secsToTimeStr(interval.stop-interval.start)}
                </td>
                <td onClick={()=>selectInterval(index)}
                    className={index === selectedInterval ? "selected" : ""}>
                    <Button icon={<DownloadOutlined/>}
                            size="small" title="Скачать" type="primary" style={{marginRight:10}}
                            onClick={()=>downloadInterval(intervals[index].start,intervals[index].stop)}
                    />
                    <Button icon={<CloseOutlined/>} type="primary" size="small" title="Удалить" danger
                            onClick={()=> onDeleteIntervalClick(index)}
                    />
                </td>
            </tr>
        )
    }

    const onTimeChange = (index, time, intervalType) => {
        const ints = [...intervals];
        document.getElementById("inputVideo").pause();
        let secs = timeStrToSecs(time);
        if (secs>parseInt(video.duration)) {
            secs = parseInt(video.duration);
        }
        ints[index][intervalType] = secs;
        setIntervals(ints);
        setSelectedInterval(index);
        changeVideoPositions(ints[index].start,ints[index].stop,
            intervalType === 'start' ? ints[index].start : ints[index].stop);
    };

    const onTimeSelect = (index, intervalType) => {
        setSelectedInterval(index);
        changeVideoPositions(intervals[index].start,intervals[index].stop,
            intervalType === 'start' ? intervals[index].start : intervals[index].stop);
    }

    const selectInterval = (index) => {
        setSelectedInterval(index);
        changeVideoPositions(intervals[index].start,intervals[index].stop,intervals[index].start);
    }

    const downloadAllIntervals = async() => {
        const zip = new JSZip();
        for (let interval of intervals) {
            const [blob, fileName] = await cutVideoInterval(interval.start, interval.stop);
            zip.file(fileName,blob)
        }
        const blob = await zip.generateAsync({
            type:'blob',
            compression: "DEFLATE",
            compressionOptions: {
                level: 9
            }
        })
        const a = document.createElement("a");
        a.download = "intervals.zip"
        a.href = URL.createObjectURL(blob);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    const downloadInterval = async(start, stop) => {
        const [blob, fileName] = await cutVideoInterval(start, stop);
        const a = document.createElement("a");
        a.download = fileName
        a.href = URL.createObjectURL(blob);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    const cutVideoInterval = async(start, stop) => {
        const data = await cutVideo(videoSrc, start, stop)
        const parts = videoFileName.split(".");
        const extension = parts.pop();
        let fileName = `${parts.join(".")}-${secsToTimeStr(start)}-${secsToTimeStr(stop)}.${extension}`;
        return [new File([data], fileName),fileName]
    }

    const onDeleteIntervalClick = (index) => {
        if (confirm("Вы действительно хотите удалить этот интервал?")) {
            const ints = [...intervals];
            ints.splice(index,1);
            setIntervals(ints);
        }
    }

    const loadFfmpeg = async() => {
        await ensureFfmpegLoaded();
    }

    return render();
}
