from pydub import AudioSegment
import os
import shutil
import librosa
import soundfile as sf
from slicer2 import Slicer
from pydub.utils import make_chunks
import yaml


root_dir = os.path.abspath('.')
input("你的系统path得有ffmpeg才能用重采样，这里我指向了根目录下的ffmpeg文件夹，要是这下面没有ffmpeg会直接用系统的,随便按一下键盘以继续")
AudioSegment.ffmpeg = root_dir+"/ffmpeg"
def ensure_output_path(input_path, output_root):
    """确保输出路径存在，根据输入路径创建相应的目录结构"""
    relative_path = os.path.relpath(os.path.dirname(input_path), input_dir)
    output_path = os.path.join(output_root, relative_path)
    os.makedirs(output_path, exist_ok=True)
    return output_path

def process_audio(file_path):
    """处理单个音频文件：检查时长，重采样并输出到保持相同目录结构的输出目录"""
    audio = AudioSegment.from_file(file_path)
    duration_seconds = len(audio) / 1000  # pydub使用毫秒表示时长
    if duration_seconds > 4:
        new_sample_rate = 44100
        audio = audio.set_frame_rate(new_sample_rate)
        output_subdir = ensure_output_path(file_path, output_dir)
        output_file = os.path.join(output_subdir, os.path.basename(file_path))
        audio.export(output_file, format=os.path.splitext(file_path)[1][1:].lower())
        print(f"Processed and exported to: {output_file}")

def main():
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.wav')): 
                file_path = os.path.join(root, file)
                process_audio(file_path)


def slice_audio_files(input_dir, output_base_dir, **kwargs):

    #递归遍历指定目录下的音频文件并使用audio-slicer进行切片，输出到相应同名目录下。

    
    # 确保基础输出目录存在
    os.makedirs(output_base_dir, exist_ok=True)
    

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.wav'): 
                file_path = os.path.join(root, file)
                rel_path_from_input = os.path.relpath(file_path, input_dir)
                output_rel_path = os.path.join(output_base_dir, rel_path_from_input)
                output_dir = os.path.dirname(output_rel_path)
                
                print(f"Processing file: {file_path}")
                try:
                    # 加载音频文件
                    audio, sr = librosa.load(file_path, sr=None, mono=False)
                    
                    # 初始化Slicer
                    slicer = Slicer(sr=sr, **kwargs)
                    
                    # 进行切片
                    chunks = slicer.slice(audio)
                    
                    # 确保输出目录存在（不重新创建，仅确认）
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # 保存切片到对应的输出目录
                    for i, chunk in enumerate(chunks):
                        if len(chunk.shape) > 1:
                            chunk = chunk.T  # 如果音频是立体声，则交换轴
                        output_file_name = f"{os.path.splitext(os.path.basename(file))[0]}_{i}.wav"
                        output_file_path = os.path.join(output_dir, output_file_name)
                        sf.write(output_file_path, chunk, sr)
                        print(f"Saved chunk: {output_file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


# 使用示例
input_directory = '/root/autodl-tmp/tmp/skip'  # 输入目录路径
output_directory = '/root/autodl-tmp/tmp/preprocess'  # 输出目录路径
# 定义Slicer参数
slicer_params = {
    'threshold': -40,
    'min_length': 5000,
    'min_interval': 300,
    'hop_size': 10,
    'max_sil_kept': 500
}




def copy_and_rename_dirs(src_dir, dst_dir, exclude_folders=None):
   
    
    # 记录原始文件夹名到新文件夹名的映射
    folder_mapping = {}
    counter = 1
    
    # 确保目标目录存在
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    # 遍历源目录下的所有子目录
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in exclude_folders]  # 过滤掉需要排除的文件夹
        for dir_name in dirs:
            src_path = os.path.join(root, dir_name)
            new_dir_name = f"{counter}"
            dst_path = os.path.join(dst_dir, new_dir_name)
            
            # 复制并重命名文件夹
            shutil.copytree(src_path, dst_path)
            
            # 只有当文件夹实际被复制时才记录映射关系
            folder_mapping[dir_name] = new_dir_name
            counter += 1
        
    # 将映射关系写入到配置文件
    with open(os.path.join(root_dir, 'speakers.yaml'), 'w', encoding='utf-8') as yaml_file:
        yaml.dump(folder_mapping, yaml_file, default_flow_style=False,allow_unicode=True,)
        
    print("映射关系构建完成，请妥善保管speakers.yaml")




def get_duration(file_path):
    """获取音频文件的时长（秒）"""
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000  # pydub 返回的是毫秒，转换为秒

def move_long_audio_files(src, dst):
    """移动时长大于 min_duration_seconds 的音频文件到目标目录"""
    for root, dirs, files in os.walk(src):
        for file in files:
            if file.endswith(".wav"):  # 根据需要修改音频文件的扩展名
                file_path = os.path.join(root, file)
                duration = get_duration(file_path)
                if duration > 20:
                    relative_path = os.path.relpath(file_path, src)
                    target_file_path = os.path.join(dst, relative_path)
                    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                    shutil.move(file_path, target_file_path)
                    print(f"Moved: {file_path} -> {target_file_path}")


input_dir =root_dir+"/input"
output_dir =root_dir+"/tmp/preprocess"
main()
move_long_audio_files(root_dir+"/tmp/preprocess", root_dir+"/tmp/skip")
slice_audio_files(root_dir+"/tmp/skip", root_dir+"/tmp/preprocess", **slicer_params)
copy_and_rename_dirs(root_dir+"/tmp/preprocess", root_dir+"/output", exclude_folders=[ '.ipynb_checkpoints'])

