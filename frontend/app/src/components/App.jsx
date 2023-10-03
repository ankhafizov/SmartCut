import {useState,useEffect} from "react"
import {Slider, Button, Tabs} from "antd";
import {CaretRightFilled, PauseOutlined, DownloadOutlined} from '@ant-design/icons';
import {secsToTimeStr} from "../utils/utils.js";
import RequestForm from "./RequestForm.jsx";
import ResultsTable from "./ResultsTable.jsx";
import {getBackendUrl} from "../config/config.js";
import "../styles/styles.css";

/**
 * Главный экран приложения
 */
function App() {
    const [startPos,setStartPos] = useState(0);
    const [endPos,setEndPos] = useState(0);
    const [currentPos,setCurrentPos] = useState(0);
    const [videoFileName, setVideoFileName] = useState("");
    const [videoSrc, setVideoSrc] = useState("");
    const [isPlaying, setIsPlaying] = useState(false);
    const [activeTab, setActiveTab] = useState('1');
    const [intervals, setIntervals] = useState([]);
    const [selectedInterval, setSelectedInterval] = useState(null);

    const video = document.getElementById("inputVideo");

    useEffect(() => {
        auth().then()
        window.scAppState = {};
        setupVideoEventListeners();
    }, [])

    const auth = async() => {
        await fetch(getBackendUrl()+"/auth")
    }

    const render = () => {
        return <>
            <div className="main">
                {renderVideoPlayer()}
            </div>
            {videoSrc && renderTabs()}
        </>
    }

    const renderVideoPlayer = () => {
        return (
            <>
                <div className="videoPlayer">
                    <strong>{videoFileName ? videoFileName : "Файл не загружен"}</strong>
                    <Button type="primary" onClick={()=>uploadVideo()} icon={<DownloadOutlined/>}>
                        Загрузить видео
                    </Button>
                </div>
                <video preload="auto" id="inputVideo" src={videoSrc}/><br/>
                {videoSrc && renderVideoControlPanel()}
            </>
        )
    }

    const renderVideoControlPanel = () => {
        return (
            <>
                <div className="videoControlPanel">
                    <Button id="playBtn" onClick={()=> onPlayClick()}
                            icon={isPlaying ? <PauseOutlined/> : <CaretRightFilled/>}
                            title={isPlaying ? "Пауза" : "Старт"}
                    />
                    <Slider className="videoSlider" value={currentPos} min={startPos} max={parseInt(endPos)}
                            tooltip={{formatter:value=>secsToTimeStr(value),open:true}}
                        onChange={pos => onSliderChange(pos)}
                    />
                    <span>{secsToTimeStr(endPos)}</span>
                </div>
            </>
        )
    }

    const renderTabs = () => {
        const tabs = [
            {
                key: '1',
                label: 'Форма запроса',
                children: <RequestForm
                    videoFileName={videoFileName}
                    videoSrc = {videoSrc}
                    endPos = {endPos}
                    setIntervals={setIntervals}
                    setSelectedInterval={setSelectedInterval}
                    activateTab={activateTab}
                    changeVideoPositions={changeVideoPositions}
                />
            },
            {
                key: '2',
                label: 'Таблица результатов',
                children: <ResultsTable
                    videoFileName={videoFileName}
                    videoSrc={videoSrc}
                    intervals={intervals}
                    setIntervals={setIntervals}
                    selectedInterval={selectedInterval}
                    setSelectedInterval={setSelectedInterval}
                    changeVideoPositions={changeVideoPositions}
                />
            },
        ];
        return (
            <div id="tabsContainer">
                <Tabs type="card" activeKey={activeTab} onTabClick = {(key) => activateTab(key) } items={tabs}/>
            </div>
        )
    }

    const activateTab = (key) => {
        setActiveTab(key)
        if (key === '1') {
            changeVideoPositions(0,video.duration,0);
        } else {
            if (intervals.length) {
                setSelectedInterval(0);
                const interval = intervals[0];
                changeVideoPositions(interval.start,interval.stop,interval.start);
            }
        }
    }

    const changeVideoPositions = (start, end, current) => {
        window.scAppState.startPos = start;
        window.scAppState.endPos = end;
        window.scAppState.currentPos = current;
        setStartPos(start);
        setEndPos(end)
        setCurrentPos(current);
        document.getElementById("inputVideo").currentTime = current;
    }

    const uploadVideo = () => {
        const input = document.createElement("input");
        input.setAttribute("type", "file");
        input.style.display = "none";
        input.addEventListener("change", (event) => {
            if (event.target.files && event.target.files.length) {
                setIsPlaying(false);
                setVideoSrc(URL.createObjectURL(event.target.files[0]))
                setVideoFileName(event.target.files[0].name);
            }
        });
        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
    }

    const onPlayClick = () => {
        if (!isPlaying) {
            video.play();
            setIsPlaying(true);
        } else {
            video.pause();
            setIsPlaying(false);
        }
    }

    const onSliderChange = (pos) => {
        video.currentTime = pos;
        setCurrentPos(pos);
    }

    const setupVideoEventListeners = () => {
        const video = document.getElementById("inputVideo");

        video.addEventListener("loadeddata", () => {
            const video = document.getElementById("inputVideo");
            setStartPos(0);
            setCurrentPos(0)
            setEndPos(parseInt(video.duration));
            window.scAppState.startPos = 0;
            window.scAppState.endPos = parseInt(video.duration);
            window.scAppState.currentPos = 0;
            video.currentTime = window.scAppState.startPos;
        })

        video.addEventListener("error", () => {
            setVideoSrc(null);
        })

        video.addEventListener("timeupdate", () => {
            const video = document.querySelector('video');
            if (video.currentTime>window.scAppState.endPos) {
                video.currentTime = window.scAppState.startPos;
                video.pause();
                setIsPlaying(false);
            } else if (video.currentTime<window.scAppState.startPos) {
                video.currentTime = window.scAppState.startPos;
            }
            setCurrentPos(video.currentTime);
            window.scAppState.currentPos = video.currentTime;
        })
    }

    return render()
}

export default App;
