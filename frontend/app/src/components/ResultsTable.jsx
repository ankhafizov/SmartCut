import {useState,useEffect} from "react";
import {Button, Modal, Progress, TimePicker} from "antd";
import {CloseOutlined, DownloadOutlined, PlusOutlined} from "@ant-design/icons";
import dayjs from "dayjs";
import {secsToTimeStr, timeStrToSecs} from "../utils/utils.js";
import {cutVideo, ensureFfmpegLoaded} from "../services/ffmpeg.js";

/**
 * Таблица видео-интервалов
 */
export default function ResultsTable(
    {videoFileName, videoSrc, intervals, setIntervals, selectedInterval,setSelectedInterval,changeVideoPositions}) {

    const video = document.getElementById("inputVideo");

    const [modalOpen, setModalOpen] = useState(false);
    const [progressModalTitle,setProgressModalTitle] = useState("");
    const [downloadPercent, setDownloadPercent] = useState(0)

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
                        <th>
                            <Button type="primary" style={{backgroundColor:"green"}} icon={<PlusOutlined/>}
                                    onClick={()=>onAddIntervalClick()}>Добавить
                            </Button>
                        </th>
                    </tr>
                    {intervals.sort((i1,i2)=>i1.start-i2.start).map((interval,index) => renderInterval(interval, index))}
                    </tbody>
                </table>
                <div style={{display:intervals.length ? "" : "none"}} className="intervalsTableFooter">
                    <Button type="primary" icon={<DownloadOutlined/>} onClick={()=>downloadAllIntervals()}>
                        Скачать все
                    </Button>
                </div>
                {renderProgressModal()}
            </>
        )
    }

    const renderInterval = (interval, index) => {
        return (
            <tr key={"interval_"+index}>
                <td onClick={()=>selectInterval(index)}
                    className={interval === selectedInterval ? "selected" : ""}>
                    <TimePicker value={dayjs(secsToTimeStr(interval.start), 'HH:mm:ss')} size="small"
                                onChange={(time,strTime) => {
                                    onTimeChange(index,strTime,'start')
                                }}
                                onSelect = {() => onTimeSelect(index,'start')}
                                changeOnBlur={true} popupStyle={{display:'none'}}
                    />

                </td>
                <td onClick={()=>selectInterval(index)}
                    className={interval === selectedInterval ? "selected" : ""}>
                    <TimePicker value={dayjs(secsToTimeStr(interval.stop), 'HH:mm:ss')} size="small"
                                onChange={(time,strTime) => {
                                    onTimeChange(index,strTime,'stop')
                                }}
                                onSelect = {() => onTimeSelect(index,'stop')}
                                changeOnBlur={true} popupStyle={{display:'none'}}
                    />
                </td>
                <td onClick={()=>selectInterval(index)}
                    className={interval === selectedInterval ? "selected" : ""}>
                    {secsToTimeStr(interval.stop-interval.start)}
                </td>
                <td onClick={()=>selectInterval(index)}
                    className={interval === selectedInterval ? "selected" : ""}>
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

    const renderProgressModal = () => {
        return (
            <Modal
                open={modalOpen}
                title=""
                footer={[
                ]}
                closeIcon={null}
            >
                <h2>Экспорт видео</h2>
                <span>{progressModalTitle}</span>
                <Progress percent={downloadPercent} />
            </Modal>
        )
    }

    const onTimeChange = (index, time, intervalType) => {
        const ints = [...intervals];
        document.getElementById("inputVideo").pause();
        let secs = timeStrToSecs(time);
        if (isNaN(secs)) {
            secs = 0;
        }
        if (secs>parseInt(video.duration)) {
            secs = parseInt(video.duration);
        }
        ints[index][intervalType] = secs;
        if (ints[index].stop < ints[index].start) {
            ints[index].start = ints[index].stop
        }
        setIntervals(ints);
        setSelectedInterval(intervals[index]);
        changeVideoPositions(ints[index].start,ints[index].stop,
            intervalType === 'start' ? ints[index].start : ints[index].stop);
    };

    const onTimeSelect = (index, intervalType) => {
        setSelectedInterval(intervals[index]);
        changeVideoPositions(intervals[index].start,intervals[index].stop,
            intervalType === 'start' ? intervals[index].start : intervals[index].stop);
    }

    const selectInterval = (index) => {
        setSelectedInterval(intervals[index]);
        changeVideoPositions(intervals[index].start,intervals[index].stop,intervals[index].start);
    }

    const downloadAllIntervals = async() => {
        const zip = new JSZip();
        setModalOpen(true);
        setProgressModalTitle("");
        setDownloadPercent(0)
        for (let index in intervals) {
            const interval = intervals[index];
            setDownloadPercent(parseInt((index)/(intervals.length+1)*100))
            const [blob, fileName] = await cutVideoInterval(interval.start, interval.stop);
            zip.file(fileName,blob)
        }
        setProgressModalTitle(`Упаковка в ZIP-архив`);
        const blob = await zip.generateAsync({
            type:'blob',
            compression: "DEFLATE",
            compressionOptions: {
                level: 9
            }
        })
        setModalOpen(false);
        downloadBlob(blob,"intervals.zip");
    }

    const downloadInterval = async(start, stop) => {
        setModalOpen(true);
        setProgressModalTitle("");
        setDownloadPercent(0);
        const [blob, fileName] = await cutVideoInterval(start, stop);
        setModalOpen(false);
        downloadBlob(blob, fileName);
    }

    const downloadBlob = (blob, fileName) => {
        const a = document.createElement("a");
        a.download = fileName
        a.href = URL.createObjectURL(blob);
        setDownloadPercent(100);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    const cutVideoInterval = async(start, stop) => {
        const parts = videoFileName.split(".");
        const extension = parts.pop();
        let fileName = `${parts.join(".")}-${secsToTimeStr(start)}-${secsToTimeStr(stop)}.${extension}`;
        setProgressModalTitle(`Экспорт ${fileName}`);
        const data = await cutVideo(videoSrc, start, stop)
        return [new File([data], fileName),fileName]
    }

    const onAddIntervalClick = () => {
        const ints = [...intervals];
        const interval = ints.push({start:0,stop:video.duration})
        setIntervals(ints);
        setSelectedInterval(interval);
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
