import {useState,useEffect} from "react";
import {Button, InputNumber, message, Modal, Progress, Select} from "antd";
import {CheckOutlined, ReloadOutlined} from "@ant-design/icons";
import FramesExtractor from "../services/FramesExtractor.js";
import {timeout, uuidv4} from "../utils/utils.js";
import {fetchWithTimeout} from "../backend/backend.js";
import {getBackendUrl} from "../config/config.js";

/**
 * Форма запроса видео-интервалов
 */
export default function RequestForm(
    {videoFileName, videoSrc, endPos, setIntervals, setSelectedInterval, activateTab, changeVideoPositions}) {

    const video = document.getElementById("inputVideo");

    const [modalOpen, setModalOpen] = useState(false);
    const [pluginsList, setPluginsList] = useState([])
    const [plugin, setPlugin] = useState("")
    const [uploadPercent, setUploadPercent] = useState(0);
    const [inferencePercent, setInferencePercent] = useState(0);
    const [period, setPeriod] = useState(5);

    const chunkSize = 50;

    useEffect(() => {
        updatePluginsList().then()
    }, []);

    const render = () => {
        return (
            <>
                <table id="requestForm">
                    <tbody>
                    <tr>
                        <td><label>Плагин</label></td>
                        <td style={{width:'100%'}}>
                            <div id="pluginControl">
                                <Select style={{width:"100%"}}
                                    defaultValue=""
                                    value={plugin.value}
                                    onChange={(value) => setPlugin(pluginsList.find(it => it.value === value))}
                                    options={pluginsList}
                                />
                                <Button title="Обновить" icon={<ReloadOutlined/>} size="small" type="link"
                                        onClick={()=>updatePluginsList()}
                                />
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <label>Период (сек)</label>
                        </td>
                        <td>
                            <InputNumber
                                style={{width:"100%"}}
                                min={0}
                                max={parseInt(endPos)}
                                value={period}
                                onChange={(value) => setPeriod(value)}
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <Button type="primary" icon={<CheckOutlined/>} onClick={()=>onGetSegmentsClick()}
                                    disabled={!period || !plugin || !plugin.value}>
                                Получить интервалы
                            </Button>
                        </td>
                    </tr>
                    </tbody>
                </table>
                {renderProgressModal()}
            </>
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
                <span>Не закрывайте эту страницу!</span>
                <h2 className="title">Передача видео</h2>
                <Progress percent={uploadPercent} />
                <h2 className="title">Обработка видео</h2>
                <Progress percent={inferencePercent} />
            </Modal>
        )
    }

    const onGetSegmentsClick = async() => {
        const uid = uuidv4();
        setUploadPercent(0);
        setInferencePercent(0);
        const error = await uploadVideo(uid);
        if (error) {
            message.error(error);
            return
        }
        setUploadPercent(100);
        await downloadResultIntervals(uid);
        setInferencePercent(100)
        setModalOpen(false);
    }

    const uploadVideo = async(uid) => {
        const response = await fetchWithTimeout(getBackendUrl()+"/create_request/"+uid);
        if (response.status !== 200) {
            return (await response.json()).detail
        }
        const extractor = new FramesExtractor();
        await extractor.init(videoSrc, plugin.size);
        const seconds = period;
        setModalOpen(true);
        setIntervals([]);
        for (let startTime = 0; startTime < video.duration; startTime += period * chunkSize) {
            setUploadPercent(parseInt(startTime/video.duration*100));
            try {
                const zip = await extractor.extract(startTime, seconds, chunkSize);
                const is_last = startTime+period*chunkSize >= video.duration
                const response = await uploadZip(uid, videoFileName, startTime + ".zip", zip, is_last);
                const json = await response.json();
                setInferencePercent(parseInt((json.processed_chunks / (video.duration/period/chunkSize))*100))
            } catch (err) {
                message.error(err.toString())
                break;
            }
        }
        extractor.destroy();
    }

    const uploadZip = async(uid, videoFileName, archiveName, zip, is_last = false, attempt= 0) => {
        const body = new FormData();
        body.append("user_request_uid", uid)
        body.append("video_file_name", videoFileName);
        body.append("plugin_name", plugin.value);
        body.append("zip", zip, archiveName);
        body.append("is_last", is_last);
        const response = await fetchWithTimeout(getBackendUrl()+`/upload_zip`, {
            method: "POST",
            body: body,
        }, 3*60*1000);
        if (response.status !== 200) {
            if (attempt < 5) {
                return await uploadZip(uid, videoFileName, archiveName, zip, is_last, attempt + 1);
            } else {
                throw Error("Ошибка передачи видео !")
            }
        }
        return response;
    }

    const downloadResultIntervals = async(uid) => {
        const detectedIntervals = await getProcessedVideoIntervals(uid);
        if (detectedIntervals && detectedIntervals.length) {
            setIntervals(detectedIntervals);
            setSelectedInterval(0);
            changeVideoPositions(detectedIntervals[0].start,detectedIntervals[0].stop,detectedIntervals[0].start);
            activateTab('2')
        } else {
            message.error("Ошибка при получении интервалов !");
        }
    }

    const getProcessedVideoIntervals = async(uid) => {
        while (true) {
            const response = await fetchWithTimeout(getBackendUrl() + "/get_video_intervals/"+uid);
            if (response.status === 200) {
                const json = await response.json();
                if (json.timestamps && typeof(json.timestamps) === "object") {
                    return json.timestamps;
                } else if (typeof(json.processed_chunks) === "number") {
                    setInferencePercent(parseInt((json.processed_chunks / (video.duration/period/chunkSize))*100))
                }
            } else if (response.status !== 404) {
                return
            }
            await timeout(5000);
        }
    }

    const updatePluginsList = async() => {
        try {
            const response = await fetchWithTimeout(getBackendUrl()+"/plugins")
            const json = await response.json();
            json.unshift({plugin_name:"", label:"Укажите плагин"})
            setPluginsList(json.map(plug => ({value: plug.plugin_name, label: plug.label, size: plug.size})));
        } catch {
            message.error("Ошибка при получении списка плагинов")
        }
    }

    return render();
}
