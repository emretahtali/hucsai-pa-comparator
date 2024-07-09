# python assignment i/o comparator // made by emre tahtalı
# anyone can modify this program according to their needs and publish it, but please give attribution.

import sys, os, subprocess, shutil, glob
from tkinter import messagebox
import customtkinter as ct
from paramiko import SSHClient
from scp import SCPClient

ct_inputs, ct_outputs, ct_codefile, ct_username, ct_password, ct_start, ct_end, ct_language, ct_additional, ct_remember, ct_keepfiles, client, root = (None,) * 13
error = user_output_str = given_output_str = ""
ct_return = []


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
    out, err, exit_stat = stdout.read(), stderr.read().decode("utf8"), stdout.channel.recv_exit_status()
    stdin.close(); stdout.close(); stderr.close()

    return out, err, exit_stat


def folder_exists(path):
    pathlist = path.split("/")

    if len(pathlist) > 1:
        mother_path = "".join(pathlist[:-1])
        path = pathlist[-1]
        command = run_command(f"ls '{mother_path}'")

    else: command = run_command(f"ls")

    dir_list = command[0].decode("utf8").split("\n")
    return path in dir_list


def got_error(text, path):
    global error, client
    error = text

    run_command(f"rm -r '{path}'")
    client.close()


def connect_and_execute():
    global ct_inputs, ct_outputs, ct_codefile, ct_username, ct_password, ct_start, ct_end, ct_language, ct_additional, ct_remember, ct_keepfiles, client, error, user_output_str, given_output_str, root

    codefile = ct_codefile.get()
    inputs = ct_inputs.get().split()
    given_outputs = ct_outputs.get().split()
    username = ct_username.get()
    password = ct_password.get()
    language = ct_language.get()
    keepfiles = ct_keepfiles.get()
    start = ct_start.get()
    end = ct_end.get()

    # for debug
    codefile = "main.py"
    inputs = ["i{}.txt"]
    given_outputs = ["o{}.txt"]
    username = "b2230356027"
    password = "Emrys22hacet+"

    # exit if there is missing info
    if not (codefile and given_outputs and username and password):
        messagebox.showerror("missing data", "please fill all the necessary boxes.")
        error = "escape"
        return

    user_outputs = [f"output{i}.txt" for i in range(len(given_outputs))]

    # constants
    MAIN_FLD = "__comparator__"
    TRASH = "trash"
    LOCALPATH = os.path.dirname(os.path.realpath(__file__))

    # connect
    client = SSHClient()
    client.load_system_host_keys()
    client.connect('dev.cs.hacettepe.edu.tr', username=username, password=password)

    # create main folder for comparator if it doesn't exist
    if not folder_exists(MAIN_FLD): run_command("mkdir " + MAIN_FLD)

    # folder name is changed if a folder with same name already exists
    folder_orig_name = LOCALPATH.split("\\")[-1]
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
    scp.put(LOCALPATH, recursive=True, remote_path=PATH)
    scp.close()

    # make a trash directory to dump the outputs of the program to be deleted later
    run_command(f"mkdir '{PATH}/{TRASH}'")

    error = user_output_str = given_output_str = ""

    # compile if java
    if language == "java":
        command = run_command(f"javac8 '{PATH}/{codefile}'")

        if command[2] != 0:
            got_error("an error occurred compiling the code.", PATH)
            return

    count = int(start) if start != "" else 1
    # while os.path.isfile("io/" + inputs[0].format(count)):

    txt1 = inputs[0].format(count)
    txt2 = run_command(f"cd '{PATH}/io';ls '{inputs[0].format(count)}'")[0].decode("utf8")
    print(txt1)
    print(txt2)
    print(str(txt1 == txt2))

    # print("", str(inputs[0].format(count) == run_command(f"cd '{PATH}/io';ls '{inputs[0].format(count)}'")[0].decode("utf8")))
    while run_command(f"cd '{PATH}/io';ls '{inputs[0].format(count)}'")[0].decode("utf8") == inputs[0].format(count):
        messagebox.showinfo("", "reached")
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
            given_output = run_command(f"cat '{PATH}/io/{user_outputs[i].format(count)}'")[0]

            # compare and write the outcome
            dashes = "\n" + 60 * "-" + "\n"

            if user_output == given_output:
                user_output_str += f"{dashes}{given_outputs[i].format(count)}: identical."
                given_output_str += f"{dashes}{given_outputs[i].format(count)}: identical."
            else:
                user_output_str += f"{dashes}{given_outputs[i].format(i)}: difference found:\n{user_output}"
                given_output_str += f"{dashes}{given_outputs[i].format(i)}: difference found:\n{given_output}"

        count += 1

    # delete the files from ssh if not wanted
    """if keepfiles:
        if folder_exists(f"'{PATH}/{TRASH}'"): run_command(f"rm -r '{PATH}/{TRASH}'")

        file_exists = not run_command(f"ls '{PATH}/{__file__}'")[2]
        if file_exists: run_command(f"rm '{PATH}/{__file__}'")
    else:
        run_command(f"rm -r '{PATH}'")"""

    client.close()


def input_line(master, text, example):
    frame = ct.CTkFrame(master=master, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    frame.pack(padx=50, fill="both", expand=True)

    ct.CTkLabel(master=frame, text=text).pack(pady=12, padx=10, side=ct.LEFT)

    ct_item = ct.CTkEntry(master=frame, placeholder_text=example)
    ct_item.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)
    return ct_item


def open_res_win():
    global root, error, user_output_str, given_output_str

    # creating the window
    res_window = ct.CTkToplevel(root)
    res_window.geometry("1200x600")

    res_window.title("comparator results")

    # title
    title_frame = ct.CTkFrame(master=res_window)
    title_frame.pack(pady=(40, 20), padx=40, fill="x")
    ct.CTkLabel(master=title_frame, text="comparator results", font=("Arial", 16, "bold")).pack(pady=12, padx=10)

    # error = "IndentationError: unindent does not match any outer indentation level\nosman"
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


def main():
    global ct_inputs, ct_outputs, ct_codefile, ct_username, ct_password, ct_start, ct_end, ct_language, ct_additional, ct_remember, ct_keepfiles, error, user_output_str, given_output_str, root

    root = ct.CTk()
    root.geometry("500x672")
    root.title("comparator")

    ct.set_appearance_mode("dark")
    ct.set_default_color_theme("dark-blue")

    frame = ct.CTkFrame(master=root)
    frame.pack(pady=20, padx=40, fill="x", expand=True)

    label = ct.CTkLabel(master=frame, text="comparator", font=("Arial", 16, "bold"))
    label.pack(pady=(24, 12), padx=10)

    #inputs
    ct_codefile = input_line(frame, "code file name:", "helloworld.py")
    ct_inputs = input_line(frame, "inputs:", "product_{}.txt purchase_{}.txt")
    ct_outputs = input_line(frame, "outputs:", "output{}.txt")
    ct_username = input_line(frame, "username:", "b<student id>")

    # password
    password_frame = ct.CTkFrame(master=frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    password_frame.pack(padx=50, fill="both", expand=True)

    ct.CTkLabel(master=password_frame, text="password:").pack(pady=12, padx=10, side=ct.LEFT)

    ct_password = ct.CTkEntry(master=password_frame, placeholder_text="******", show="*")
    ct_password.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)

    # run button
    run_frame = ct.CTkFrame(master=frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    run_frame.pack(padx=50, fill="both", expand=True)

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

    ct_additional = ct.CTkCheckBox(master=checkbox_frame, text="additional options", command=additional_button)
    ct_additional.pack(pady=12, padx=10, side=ct.LEFT)

    # TODO: add remember functionality
    ct_remember = ct.CTkCheckBox(master=checkbox_frame, text="remember settings")
    ct_remember.pack(pady=12, padx=10, side=ct.RIGHT)

    # additional options
    additional_frame = ct.CTkFrame(master=root)

    # ask for keeping the files
    keep_frame = ct.CTkFrame(master=additional_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    keep_frame.pack(pady=(12, 0), padx=50, fill="both", expand=True)

    ct_keepfiles = ct.CTkCheckBox(master=keep_frame, text="keep the files in remote")
    ct_keepfiles.pack(pady=12, padx=10, side=ct.LEFT)

    # start index
    start_frame = ct.CTkFrame(master=additional_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    start_frame.pack(padx=50, fill="both", expand=True)

    ct.CTkLabel(master=start_frame, text="start index:").pack(pady=12, padx=10, side=ct.LEFT)

    ct_start = ct.CTkEntry(master=start_frame, placeholder_text="0")
    ct_start.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)

    # end index
    end_frame = ct.CTkFrame(master=additional_frame, fg_color=ct.ThemeManager.theme["CTkFrame"]["fg_color"])
    end_frame.pack(pady=(0, 12), padx=50, fill="both", expand=True)

    ct.CTkLabel(master=end_frame, text="end index:").pack(pady=12, padx=10, side=ct.LEFT)

    ct_end = ct.CTkEntry(master=end_frame, placeholder_text="10")
    ct_end.pack(pady=12, padx=10, fill="x", expand=True, side=ct.RIGHT)

    root.mainloop()


if __name__ == "__main__": main()