/**
 * Сервис для извлечения кадров из видео и создания
 * из них zip-архивов
 * @constructor
 */
export default function FramesExtractor() {

    this.video = document.createElement("video");
    this.video.style.display = 'none';
    this.canvas = document.createElement("canvas");
    this.canvas.style.display = 'none';
    document.body.appendChild(this.video);
    document.body.appendChild(this.canvas);

    this.videoWidth = 0;
    this.videoHeight = 0;
    this.zip = new JSZip();
    this.currentNumFiles = 0;

    this.init = (videoSrc, longSideSize) => {
        this.subscribers = {};
        return new Promise(resolve => {
            this.setEventListeners();
            this.subscribers.loadeddata = () => {
                this.video.currentTime = 0;
                const coef = Math.min(this.video.videoWidth,this.video.videoHeight) /
                    Math.max(this.video.videoWidth, this.video.videoHeight);
                if (this.video.videoWidth > this.video.videoHeight) {
                    this.canvas.width = longSideSize;
                    this.canvas.height = longSideSize * coef;
                } else {
                    this.canvas.height = longSideSize;
                    this.canvas.width = longSideSize * coef;
                }
                resolve();
            }
            this.video.src = videoSrc;
        });
    }

    this.extract = (startTime=0,period=10,numFrames=50) => {
        return new Promise(async(resolve,reject) => {
            try {
                this.zip = new JSZip();
                this.numFrames = numFrames;
                this.period = period;
                this.currentNumFiles = 0;
                this.subscribers.zipGenerated = (zip) => {
                    resolve(zip);
                }
                if (this.video.currentTime) {
                    this.video.currentTime = startTime;
                } else {
                    await this.addFileToZip();
                    this.currentNumFiles = 1;
                    if (this.video.duration - this.period >= 0) {
                        this.video.currentTime += this.period;
                    } else {
                        await this.generateZip();
                    }
                }
            } catch (err) {
                reject(err);
            }
        })

    }

    this.setEventListeners = () => {
        this.video.addEventListener("loadeddata", () => {
            this.subscribers.loadeddata();
        })
        this.video.addEventListener("seeked", async(event) => {
            if (this.video.currentTime>=this.video.duration || this.currentNumFiles >= this.numFrames) {
                await this.generateZip();
            } else if (this.video.currentTime !== 0) {
                await this.addFileToZip();
                this.currentNumFiles +=1;
                this.video.currentTime += this.period;
            }
        })
    }

    this.destroy = () => {
        document.body.removeChild(this.video);
        document.body.removeChild(this.canvas);
    }

    this.getJpeg = async() => {
        return new Promise(resolve => {
            const ctx = this.canvas.getContext("2d");
            ctx.drawImage(this.video,0,0,this.canvas.width,this.canvas.height);
            this.canvas.toBlob((blob) => {
                resolve(blob)
            },"image/jpeg", 1);
        })
    }

    this.addFileToZip = () => {
        return new Promise(async(resolve) => {
            const jpeg = await this.getJpeg();
            this.zip.file(parseInt(this.video.currentTime)+".jpg",jpeg);
            resolve();
        });
    }

    this.generateZip = async() => {
        const zip = await this.zip.generateAsync({
            type:'blob',
            compression: "DEFLATE",
            compressionOptions: {
                level: 9
            }
        })
        this.subscribers.zipGenerated(zip);
    }
}
