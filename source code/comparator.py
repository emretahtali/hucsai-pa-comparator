# hu cs&ai python and java assignment i/o comparator // made by emre tahtalı in 2024
# anyone can modify this program according to their needs and publish it, but please give attribution.

import os
import sys
import webbrowser

import customtkinter as ct
from pyglet.resource import get_settings_path
from tkinter import messagebox
from PIL import Image
from paramiko import SSHClient
from scp import SCPClient

ct_mainfolder, ct_inputs, ct_outputs, ct_codefile, ct_username, ct_password, ct_start, ct_end, ct_language, ct_additional, ct_remember, ct_keepfiles, client, root = (None for _ in range(14))
error = user_output_str = given_output_str = ""
ct_return = []


def connect_and_execute():
    global ct_mainfolder, ct_inputs, ct_outputs, ct_codefile, ct_username, ct_password, ct_start, ct_end, ct_language, ct_additional, ct_remember, ct_keepfiles, client, error, user_output_str, given_output_str, root

    local_path = ct_mainfolder.get()
    codefile = ct_codefile.get()
    inputs = ct_inputs.get().split()
    given_outputs = ct_outputs.get().split()
    username = ct_username.get()
    password = ct_password.get()
    language = ct_language.get()
    remember = ct_remember.get()
    keepfiles = ct_keepfiles.get()
    start = ct_start.get()
    end = ct_end.get()

    # exit if there is missing info
    if not (local_path and codefile and given_outputs and username and password):
        messagebox.showerror("missing data", "please fill all the necessary boxes.")
        error = "escape"
        return

    user_outputs = [f"output{i}.txt" for i in range(len(given_outputs))]

    # constants
    MAIN_FLD = "__comparator__"
    TRASH = "trash"

    # save settings if remember is checked
    if remember:
        SAVE_FLD = get_settings_path("HUCSAI PA Comparator")
        if not os.path.exists(SAVE_FLD):
            os.mkdir(SAVE_FLD)

        with open(f"{SAVE_FLD}\\settings.txt", "w") as f:
            f.write("\n".join(map(str, (local_path, codefile, ct_inputs.get(), ct_outputs.get(), username, language, remember, keepfiles, start, end))))

    else:
        SAVE_FILE = get_settings_path("HUCSAI PA Comparator\\settings.txt")
        if os.path.isfile(SAVE_FILE):
            os.remove(SAVE_FILE)

    # connect
    client = SSHClient()
    client.load_system_host_keys()
    client.connect('dev.cs.hacettepe.edu.tr', username=username, password=password)

    # create main folder for comparator if it doesn't exist
    if not folder_exists(MAIN_FLD): run_command("mkdir " + MAIN_FLD)

    # folder name is changed if a folder with same name already exists
    folder_orig_name = local_path.split("\\")[-1]
    if folder_exists(MAIN_FLD + "/" + folder_orig_name):
        count = 1
        while True:
            folder_name = f"{folder_orig_name}_{str(count)}"
            if not folder_exists(MAIN_FLD + "/" + folder_name): break
            count += 1
    else: folder_name = folder_orig_name

    PATH = MAIN_FLD + "/" + folder_name

    # send current folder using scp
    scp = SCPClient(client.get_transport())
    scp.put(local_path, recursive=True, remote_path=PATH)
    scp.close()

    # make a trash directory to dump the outputs of the program to be deleted later
    run_command(f"mkdir '{PATH}/{TRASH}'")

    error = user_output_str = given_output_str = ""

    # compile if java
    if language == "java":
        dir_list = run_command(f"ls '{PATH}'")[0].split("\n")
        dir_list = filter(lambda i: ".java" in i, dir_list)

        command = run_command(f"cd '{PATH}';javac8 {' '.join(dir_list)}")

        if command[2] != 0:
            got_error(f"an error occurred while compiling the code.\n\n{command[1]}", PATH)
            return

    count = int(start) if start != "" else 1
    while os.path.isfile(local_path + "/io/" + inputs[0].format(count)):
        # break if limit exists and is reached
        if end != "" and count > int(end): break

        # run the given python file
        run_str = f"cd '{PATH}';"
        run_str += f"python3 '{codefile}'" if language == "python" else f"java8 '{codefile.strip('.java')}'"
        run_str += "".join([f" 'io/{i.format(count)}'" for i in inputs])
        run_str += "".join([f" '{TRASH}/{i}'" for i in user_outputs])

        command = run_command(run_str)
        if command[2] != 0:
            got_error(f"an error occurred while executing input {count}.\n\n{command[1]}", PATH)
            return

        # compare every output with the given outputs
        for i in range(len(given_outputs)):
            # get the texts
            user_output = run_command(f"cat '{PATH}/{TRASH}/{user_outputs[i]}'")[0]
            given_output = run_command(f"cat '{PATH}/io/{given_outputs[i].format(count)}'")[0]

            # compare and write the outcome
            dashes = "\n" + 60 * "-" + "\n"

            if user_output == given_output:
                user_output_str += f"{dashes}{given_outputs[i].format(count)}: identical."
                given_output_str += f"{dashes}{given_outputs[i].format(count)}: identical."
            else:
                user_output_str += f"{dashes}{given_outputs[i].format(count)}: difference found:{dashes}{user_output}"
                given_output_str += f"{dashes}{given_outputs[i].format(count)}: difference found:{dashes}{given_output}"

        count += 1

    # last touches to the outputs
    user_output_str += "\n" + 60 * "-"
    given_output_str += "\n" + 60 * "-"
    user_output_str = user_output_str.strip("\n")
    given_output_str = given_output_str.strip("\n")

    # delete the files from ssh if not wanted
    if keepfiles: run_command(f"rm -r '{PATH}/{TRASH}'")
    else: run_command(f"rm -r '{PATH}'")

    client.close()


def run():
    global error, client

    try: connect_and_execute()
    except Exception as e:
        error = f"an error occured.\n\n{e}"
        client.close()

    if error == "escape": return

    open_res_win()


def run_command(command):
    global client

    stdin, stdout, stderr = client.exec_command(command)
    out, err, exit_stat = stdout.read().decode("utf8"), stderr.read().decode("utf8"), stdout.channel.recv_exit_status()
    stdin.close(); stdout.close(); stderr.close()

    return out, err, exit_stat


def folder_exists(path):
    pathlist = path.split("/")

    if len(pathlist) > 1:
        mother_path = "".join(pathlist[:-1])
        path = pathlist[-1]
        command = run_command(f"ls '{mother_path}'")

    else: command = run_command(f"ls")

    dir_list = command[0].split("\n")
    return path in dir_list


def got_error(text, path):
    global error, client
    error = text

    run_command(f"rm -r '{path}'")
    client.close()


def resource(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def header_watermark(root, hover_theme):
    # watermark elements
    header = ct.CTkFrame(master=root, fg_color=ct.ThemeManager.theme["CTkLabel"]["fg_color"])
    header.pack(pady=(2, 0), padx=0, fill="x", expand=False)

    image = ct.CTkImage(light_image=Image.open(resource("github-logo.png")), dark_image=Image.open(resource("github-logo.png")))
    button = ct.CTkButton(master=header, text="github", fg_color=ct.ThemeManager.theme["CTkLabel"]["fg_color"], width=0, image=image,
                          hover_color=ct.ThemeManager.theme[hover_theme]["fg_color"], font=("Arial", 14, "italic"), text_color="#595959",
                          command=(lambda: webbrowser.open_new_tab("https://github.com/emretahtali/hucsai-pa-comparator")))
    button.pack(padx=(0, 10), side=ct.RIGHT)

    button = ct.CTkButton(master=header, text="emre tahtalı 2024",
                          fg_color=ct.ThemeManager.theme["CTkLabel"]["fg_color"], width=0, text_color="#595959",
                          hover_color=ct.ThemeManager.theme[hover_theme]["fg_color"], font=("Arial", 14, "italic"),
                          command=(lambda: webbrowser.open_new_tab("https://github.com/emretahtali")))
    button.pack(padx=0, side=ct.RIGHT)


def open_res_win():
    global root, error, user_output_str, given_output_str

    # creating the window
    res_window = ct.CTkToplevel(root)
    res_window.geometry("1200x600")
    res_window.title("comparator results")
    header_watermark(res_window, "CTkEntry")

    # title
    title_frame = ct.CTkFrame(master=res_window)
    title_frame.pack(pady=(20, 20), padx=40, fill="x")
    ct.CTkLabel(master=title_frame, text="comparator results", font=("Arial", 16, "bold")).pack(pady=12, padx=10)

    # show error screen if there is any
    if error != "":
        txt_frame = ct.CTkFrame(master=res_window)
        txt_frame.pack(pady=(20, 40), padx=40, fill="both", expand=True)

        txt_box = ct.CTkTextbox(master=txt_frame, font=("Arial", 14, "normal"), fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
        txt_box.pack(pady=10, padx=10, fill="both", expand=True)
        txt_box.insert("end", error)

    else:
        # mainframe
        txt_mainframe = ct.CTkFrame(master=res_window, fg_color=ct.ThemeManager.theme["CTkToplevel"]["fg_color"])
        txt_mainframe.pack(pady=(0, 40), padx=40, fill="both", expand=True)

        # left frame
        l_frame = ct.CTkFrame(master=txt_mainframe, fg_color=ct.ThemeManager.theme["CTkToplevel"]["fg_color"])
        l_frame.pack(padx=(0, 20), fill="both", expand=True, side=ct.LEFT)

        txt_title_l = ct.CTkFrame(master=l_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["top_fg_color"])
        txt_title_l.pack(fill="x", side=ct.TOP, pady=(0, 20))
        ct.CTkLabel(master=txt_title_l, text="expected", font=("Arial", 14, "bold")).pack(pady=12, padx=10)

        txt_frame_l = ct.CTkFrame(master=l_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
        txt_frame_l.pack(fill="both", expand=True, side=ct.BOTTOM)

        txt_box = ct.CTkTextbox(master=txt_frame_l, font=("Arial", 14, "normal"), fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
        txt_box.pack(pady=10, padx=10, fill="both", expand=True)
        txt_box.insert("end", given_output_str)

        # right frame
        r_frame = ct.CTkFrame(master=txt_mainframe, fg_color=ct.ThemeManager.theme["CTkToplevel"]["fg_color"])
        r_frame.pack(padx=(20, 0), fill="both", expand=True, side=ct.RIGHT)

        txt_title_r = ct.CTkFrame(master=r_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["top_fg_color"])
        txt_title_r.pack(fill="x", side=ct.TOP, pady=(0, 20))
        ct.CTkLabel(master=txt_title_r, text="received", font=("Arial", 14, "bold")).pack(pady=12, padx=10)

        txt_frame_r = ct.CTkFrame(master=r_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
        txt_frame_r.pack(fill="both", expand=True, side=ct.BOTTOM)

        txt_box = ct.CTkTextbox(master=txt_frame_r, font=("Arial", 14, "normal"), fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
        txt_box.pack(pady=10, padx=10, fill="both", expand=True)
        txt_box.insert("end", user_output_str)


def input_line(master, text, example, default_text):
    frame = ct.CTkFrame(master=master, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    frame.pack(padx=50, fill="both", expand=True)

    ct.CTkLabel(master=frame, text=text).pack(pady=12, padx=10, side=ct.LEFT)

    ct_item = ct.CTkEntry(master=frame, placeholder_text=example)
    if default_text != "": ct_item.insert(ct.END, default_text)
    ct_item.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)
    return ct_item


def main_screen(saved_settings):
    global ct_mainfolder, ct_inputs, ct_outputs, ct_codefile, ct_username, ct_password, ct_start, ct_end, ct_language, ct_additional, ct_remember, ct_keepfiles, error, user_output_str, given_output_str, root

    # set the scene up
    root = ct.CTk()
    root.geometry("500x738")
    root.title("comparator")

    ct.set_appearance_mode("dark")
    ct.set_default_color_theme("dark-blue")
    header_watermark(root, "CTk")

    # main frame
    main_frame = ct.CTkFrame(master=root, fg_color=ct.ThemeManager.theme["CTkLabel"]["fg_color"])
    main_frame.pack(pady=(2, 0), padx=0, fill="both", expand=True)

    frame = ct.CTkFrame(master=main_frame)
    frame.pack(pady=(0, 20), padx=40, fill="x", expand=True)

    label = ct.CTkLabel(master=frame, text="comparator", font=("Arial", 16, "bold"))
    label.pack(pady=(24, 12), padx=10)

    # inputs
    ct_mainfolder = input_line(frame, "folder path:", "C:\\Users\\user\\Desktop\\somefolder", saved_settings[0])
    ct_codefile = input_line(frame, "main file name:", "helloworld.py", saved_settings[1])
    ct_inputs = input_line(frame, "inputs:", "product_{}.txt purchase_{}.txt", saved_settings[2])
    ct_outputs = input_line(frame, "outputs:", "output{}.txt", saved_settings[3])
    ct_username = input_line(frame, "username:", "b<student id>", saved_settings[4])

    # password
    password_frame = ct.CTkFrame(master=frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    password_frame.pack(padx=50, fill="both", expand=True)

    ct.CTkLabel(master=password_frame, text="password:").pack(pady=12, padx=10, side=ct.LEFT)

    ct_password = ct.CTkEntry(master=password_frame, placeholder_text="******", show="*")
    ct_password.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)

    # run button
    run_frame = ct.CTkFrame(master=frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    run_frame.pack(padx=50, fill="both", expand=True)

    if saved_settings[5] != "":
        ct_language_def = ct.StringVar()
        ct_language_def.set(saved_settings[5])
        ct_language = ct.CTkOptionMenu(master=run_frame, values=["python", "java"], variable=ct_language_def)
    else:
        ct_language = ct.CTkOptionMenu(master=run_frame, values=["python", "java"])

    ct_language.pack(pady=12, padx=10, fill="x", expand=True, side=ct.LEFT)

    run_button = ct.CTkButton(master=run_frame, text="run", command=run)
    run_button.pack(pady=12, padx=10, side=ct.RIGHT)

    # checkboxes
    def additional_button():
        if ct_additional.get(): additional_frame.pack(pady=(0, 20), padx=40, fill="x", expand=True)
        else: additional_frame.forget()

    checkbox_frame = ct.CTkFrame(master=frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    checkbox_frame.pack(pady=(0, 12), padx=50, fill="both", expand=True)

    ct_additional = ct.CTkCheckBox(master=checkbox_frame, text="additional settings", command=additional_button)
    ct_additional.pack(pady=12, padx=10, side=ct.LEFT)

    if saved_settings[6] != "":
        ct_remember_def = ct.IntVar()
        ct_remember_def.set(int(saved_settings[6]))
        ct_remember = ct.CTkCheckBox(master=checkbox_frame, text="remember settings", variable=ct_remember_def)
    else:
        ct_remember = ct.CTkCheckBox(master=checkbox_frame, text="remember settings")

    ct_remember.pack(pady=12, padx=10, side=ct.RIGHT)

    # additional settings
    additional_frame = ct.CTkFrame(master=main_frame)

    # ask for keeping the files
    keep_frame = ct.CTkFrame(master=additional_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    keep_frame.pack(pady=(12, 0), padx=50, fill="both", expand=True)

    if saved_settings[7] != "":
        ct_keepfiles_def = ct.IntVar()
        ct_keepfiles_def.set(int(saved_settings[7]))
        ct_keepfiles = ct.CTkCheckBox(master=keep_frame, text="keep the files in remote", variable=ct_keepfiles_def)
    else:
        ct_keepfiles = ct.CTkCheckBox(master=keep_frame, text="keep the files in remote")

    ct_keepfiles.pack(pady=12, padx=10, side=ct.LEFT)

    # start index
    start_frame = ct.CTkFrame(master=additional_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    start_frame.pack(padx=50, fill="both", expand=True)

    ct.CTkLabel(master=start_frame, text="start index:").pack(pady=12, padx=10, side=ct.LEFT)

    ct_start = ct.CTkEntry(master=start_frame, placeholder_text="0")
    if saved_settings[8] != "": ct_start.insert(ct.END, saved_settings[7])
    ct_start.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)

    # end index
    end_frame = ct.CTkFrame(master=additional_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    end_frame.pack(pady=(0, 12), padx=50, fill="both", expand=True)

    ct.CTkLabel(master=end_frame, text="end index:").pack(pady=12, padx=10, side=ct.LEFT)

    ct_end = ct.CTkEntry(master=end_frame, placeholder_text="10")
    if saved_settings[9] != "": ct_end.insert(ct.END, saved_settings[8])
    ct_end.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)

    # mainloop
    root.mainloop()


def main():
    # get saved settings
    SAVE_FILE = get_settings_path("HUCSAI PA Comparator\\settings.txt")
    if os.path.isfile(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            saved_settings = f.read().split("\n")
    else:
        saved_settings = ["" for _ in range(10)]

    # start the application
    main_screen(saved_settings)


if __name__ == "__main__": main()