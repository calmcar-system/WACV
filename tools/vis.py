import os
import json
import cv2
import numpy as np
import pdb

class GTVisual(object):
    color = list()
    for i in range(27):
        color_B = 127 * int(i/9) + 1
        color_G = 127 * int((i%9)/3) + 1
        color_R = 127 * int(i%3) + 1
        if color_B + color_G + color_R > 300:
            color.append((color_B, color_G, color_R))
    key2file = {
        1: '_fovs1',
        3: '_fovs3',
        4: '_fovs5',
        2: '_fovs6',
    }
    interval = 50

    def __init__(self, data_dir, mode):
        super().__init__()
        self.data_dir = data_dir
        self.mode = mode

    def _get_color(self, index):
        idx = index % len(self.color)
        return self.color[idx]

    def _mode_read(self, frame_id):
        images = dict()
        if self.mode == 'video':
            while frame_id > self.last_frame:
                self.last_frame += 1
                for key in self.capture:
                    succes, images[key] = self.capture[key].read()
                    text = '{} camera_id:{}'.format(self.key2file[key], key)
                    text_point = (600, 65)
                    cv2.putText(images[key], text, text_point,
                        cv2.FONT_HERSHEY_SIMPLEX, 2.0, (32, 128, 255), 4)
            return images

        elif self.mode == 'image':
            for key in self.key2file:
                if '_' in self.video_name:
                    fov_name = self.video_name.split('_')[0] + self.key2file[key]
                else:
                    fov_name = self.video_name + self.key2file[key]
                sequence_path = os.path.join(
                    self.data_dir, self.video_name, fov_name, str(frame_id)+'.png')
                images[key] = cv2.imread(sequence_path)
            return images

    def _draw_frame(self, frame):
        frame_id = frame['frame_id']
        frame_anno = frame['objects']
        images = self._mode_read(frame_id)

        for anno in frame_anno:
            camera_id = anno['camera_id']
            obj_type = anno['type']
            obj_id = anno['obj_id']
            bbox = anno['bbox']
            color = self._get_color(obj_id)
            cv2.rectangle(images[camera_id], (int(bbox[0]), int(bbox[1])),
                          (int(bbox[2]), int(bbox[3])), color, 3)
            text = 'id:{} {}'.format(obj_id, obj_type)
            text_point = (int(bbox[0] + 10), int(bbox[1]/2 + bbox[3]/2))
            cv2.putText(images[camera_id], text, text_point,
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

        # put four camera output images in a single cv_window
        img_w = images[1].shape[1] * 2 + self.interval
        img_h = images[1].shape[0] * 2 + self.interval
        img_c = images[1].shape[2]
        cv_image = np.zeros((img_h, img_w, img_c), dtype=np.uint8)

        cv_image[0: images[1].shape[0], 0: images[1].shape[1], :] = images[1]
        cv_image[0: images[1].shape[0], images[1].shape[1] + self.interval: img_w, :] = images[2]
        cv_image[images[1].shape[0]+self.interval: img_h, 0: images[1].shape[1], :] = images[3]
        cv_image[images[1].shape[0]+self.interval: img_h, images[1].shape[1]+self.interval: img_w, :] = images[4]
        return cv_image

    def show_result(self, gt_path):
        with open(gt_path, 'r') as f:
            self.gt = json.load(f)
        self.video_name = os.path.splitext(os.path.basename(gt_path))[0]
        cv2.namedWindow('Test', cv2.WINDOW_NORMAL)

        if self.mode == 'video':
            self.capture = dict()
            for key in self.key2file:
                if '_' in self.video_name:
                    fov_name = self.video_name.split('_')[0] + self.key2file[key]
                else:
                    fov_name = self.video_name + self.key2file[key]
                video_path = os.path.join(self.data_dir, fov_name+'.mp4')
                self.capture[key] = InitCapture(video_path)
            self.last_frame = -1
        elif self.mode == 'image':
            pass
        
        wait_time = 0
        for frame in self.gt:
            cv_image = self._draw_frame(frame)
            cv2.imshow('Test', cv_image)
            key_input = cv2.waitKey(wait_time)
            if key_input == 27:
                exit(0)
            elif key_input == 0:
                wait_time = 0
            elif key_input == 13:
                wait_time = 50

def InitCapture(path):
    if not os.path.exists(path):
        print("video %s does not exist" % path)
        exit(0)
    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        print("open video %s failed" % path)
        exit(0)
    return capture

if __name__ == '__main__':
    config_path = os.path.join('tools', 'config', 'vis.json') # to support different os
    with open(config_path, 'r') as f:
        config = json.load(f)
    gt_vis = GTVisual(config['data_dir'], config['mode'])

    gt_name = os.path.split(config['data_dir'])[1] + '.json'
    gt_path = os.path.join(config['data_dir'], gt_name)
    gt_vis.show_result(gt_path)
