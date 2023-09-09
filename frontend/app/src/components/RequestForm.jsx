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
    const [uploadStepTitle, setUploadStepTitle] = useState("Передача видео");
    const [period, setPeriod] = useState(5);

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
                <h2 className="title">{uploadStepTitle}</h2>
                <span>Не закрывайте эту страницу!</span>
                <Progress percent={uploadPercent} />
            </Modal>
        )
    }

    const onGetSegmentsClick = async() => {
        try {
            const uid = uuidv4();
            await uploadVideo(uid);
            await postIntervalsRequest(uid);
            setUploadPercent(100);
            setUploadStepTitle("Ожидание результата");
            await downloadResultIntervals(uid);
        } catch (err) {
            message.error("Ошибка получения интервалов: " + err.toString());
        } finally {
            setModalOpen(false);
        }
    }

    const postIntervalsRequest = async(uid) => {
        await fetchWithTimeout(getBackendUrl()+`/post_video_to_plugin/${uid}/${plugin.value}/${videoFileName}`);
    }

    const uploadVideo = async(uid) => {
        const extractor = new FramesExtractor();
        await extractor.init(videoSrc, plugin.size);
        const numFrames = 50;
        const seconds = period;
        setUploadStepTitle("Передача видео")
        setUploadPercent(0)
        setModalOpen(true);
        setIntervals([]);
        for (let startTime = 0; startTime < video.duration; startTime += period * numFrames) {
            setUploadPercent(parseInt(startTime/video.duration*100));
            const zip = await extractor.extract(startTime, seconds, numFrames);
            await uploadZip(uid, videoFileName, startTime + ".zip", zip);
        }
        extractor.destroy();
    }

    const uploadZip = async(uid, videoFileName, archiveName, zip, attempt=0) => {
        try {
            const body = new FormData();
            body.append("uid", uid);
            body.append("video_file_name", videoFileName);
            body.append("zip", zip, archiveName);
            await fetchWithTimeout(getBackendUrl()+`/upload_zip`, {
                method: "POST",
                body: body,
            }, 3*60*1000);
        } catch (err) {
            console.error(err);
            if (attempt<5) {
                await uploadZip(uid, videoFileName, archiveName, zip,attempt+1);
            } else {
                throw err;
            }
        }
    }

    const downloadResultIntervals = async(uid) => {
        await timeout(5000);
        const detectedIntervals = await getProcessedVideoIntervals(uid);
        if (detectedIntervals && detectedIntervals.length) {
            setIntervals(detectedIntervals);
            setSelectedInterval(0);
            changeVideoPositions(detectedIntervals[0].start,detectedIntervals[0].stop,detectedIntervals[0].start);
            activateTab('2')
        } else {
            message.error("Интервалы не обнаружены");
        }
    }

    const getProcessedVideoIntervals = async(uid) => {
        try {
            while (true) {
                const response = await fetchWithTimeout(getBackendUrl() + "/get_video_intervals/"+uid);
                if (response.status === 200) {
                    const json = await response.json();
                    return json.timestamps;
                }
                await timeout(10000);
            }
        } catch (err) {
            await timeout(10000);
            return await getProcessedVideoIntervals(uid);
        }
    }

    const updatePluginsList = async() => {
        try {
            const response = await fetchWithTimeout(getBackendUrl()+"/plugins")
            const json = await response.json();
            json.unshift({plugin_name:"", label:"Укажите плагин"})
            setPluginsList(json.map(plug => ({value: plug.plugin_name, label: plug.label, size: plug.size})));
        } catch (err) {
            message.error("Ошибка при получении списка плагинов: "+err.toString())
        }
    }

    return render();
}
