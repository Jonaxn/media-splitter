import subprocess
import os
import datetime
import argparse


def fourbit_prefix(prefix_count):
    return "{:04d}".format(int(prefix_count))

def format_timedelta(td):
    days, seconds = td.days, td.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Customize the format as needed
    icroseconds_str = f"{td.microseconds:06d}"[:3]  
    return f"{minutes:02d}:{seconds:02d}.{icroseconds_str}"

def new_timestamp_line(line, offset):
    time_format = "%M:%S.%f"
    one_line_start, one_line_end = [i.strip() for i in line.split("-->")]
    one_line_start = datetime.datetime.strptime(one_line_start, time_format)
    one_line_end = datetime.datetime.strptime(one_line_end, time_format)

    new_start_time = one_line_start - offset
    new_end_time = one_line_end - offset
        
    new_timestamp = format_timedelta(new_start_time) + " --> " + format_timedelta(new_end_time) + '\n'
    
    return new_timestamp

def create_and_write_vtt(lines: list, filename):
    # Header of the VTT file    vtt_header = "WEBVTT\n\n"
    lines.insert(0, "WEBVTT\n\n")
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as file:
        file.writelines(lines)
        
def split_subtitles(
    sub_file_path, 
    audio_file_path,
    line_amount
):
    
    path, filename = os.path.split(sub_file_path)
    filename_without_extension = filename.split(".vtt")[0]
    _, file_type = os.path.splitext(audio_file_path)
    
    
    if file_type == ".mp3":
        code_arg = "-acodec"
    else:
        code_arg = "-vcodec"
    
    line_count = 0
    
    sub_lines = []
    
    with open(sub_file_path, 'r') as f:
        lines = f.readlines()
        prefix_count = 0
        audio_start, audo_end = None, None
        index = 0
        while index < len(lines):
            line = lines[index]        
            if "-->" not in line:
                index += 1
                continue
            
            sentence = lines[index + 1] 
            
            if line_count == 0:
                audio_start, _ = [i.strip() for i in line.split("-->")]
                offset = datetime.datetime.strptime(audio_start, "%M:%S.%f")                              
             
            ntl = new_timestamp_line(line, offset)
            sub_lines.append(ntl)
            sub_lines.append(sentence)
            sub_lines.append('\n')
            
            if line_count == line_amount - 1:
                line_count = 0
                audio_sub_file_output = os.path.join(path, fourbit_prefix(prefix_count) + filename_without_extension + file_type)
                vtt_sub_file_output = os.path.join(path, fourbit_prefix(prefix_count) + filename_without_extension + '.vtt')
                
                
                _, audo_end = [i.strip() for i in line.split("-->")]
                print(audio_start, audo_end, audio_sub_file_output, ["ffmpeg", "-i", audio_file_path,
                    "-ss", audio_start, "-to", audo_end, code_arg, "copy", audio_sub_file_output])
                
                subprocess.run(
                    ["ffmpeg", "-i", audio_file_path,
                    "-ss", audio_start, "-to", audo_end, code_arg, "copy", audio_sub_file_output]
                    )
                create_and_write_vtt(sub_lines, vtt_sub_file_output)

                # re inilizie
                sub_lines = []
                prefix_count += 1

            else:
                line_count += 1
            
            index += 1


def generate_vtt_file(file_path):
    
    subprocess.run(
                    ["whisper", 
                     "--output_format", "vtt", 
                     "--output_dir", os.path.dirname(file_path),
                     file_path]
                    )
    
def main():
    parser = argparse.ArgumentParser(description="media splitter")
    
    parser.add_argument("-f", "--file", dest="filename",  help="media file")
    parser.add_argument("-l", "--lines_amount", dest="lines_amount", type=int, default=10, help="Split or chunk size in lines, for example 10 lines per file")

    args = parser.parse_args()

    media = args.filename
    lines_amount = args.lines_amount
    
    generate_vtt_file(media)
    media_full_path, _ = os.path.splitext(media)
    vtt_file_paht = media_full_path + ".vtt"
    split_subtitles(vtt_file_paht, media, lines_amount)

if __name__ == '__main__':
    main()