import csv
import sys
import tkinter as tk
from contextlib import nullcontext
from datetime import datetime
from os.path import expanduser
from tkinter import filedialog
from tkinter.messagebox import showerror
from tkinter.ttk import Label, Entry, Button, Checkbutton
from typing import List, Optional

import validators
from ttkthemes import ThemedTk

from feedscraper import Field, Post, Comment
from feedscraper.feed import GroupFeed, Feed, PageFeed


def hint(entry, hint_text):
    def handle_focus_in(_):
        if entry.get() == hint_text:
            entry.delete(0, tk.END)
        entry.config(foreground='black')

    def handle_focus_out(_):
        if not entry.get():
            entry.delete(0, tk.END)
            entry.config(foreground='grey')
            entry.insert(0, hint_text)

    entry.config(foreground='grey')
    entry.insert(0, hint_text)

    entry.bind("<FocusIn>", handle_focus_in)
    entry.bind("<FocusOut>", handle_focus_out)


def file_picker_cmd(btn, row, var: tk.StringVar, file_label=None, directory=False):
    if directory:
        filename = filedialog.askdirectory(initialdir=expanduser('~'),
                                           title='Select directory to collect data into',
                                           mustexist=True)
    else:
        filename = filedialog.asksaveasfilename(initialdir=expanduser('~'),
                                                title='Select file to collect data into',
                                                filetypes=(('CSV files', '*.csv'), ('all files', '*.*')))
    var.set(filename)
    if file_label is None:
        file_label = Label()
    if len(filename) <= 35:
        file_label.config(text=filename)
    else:
        file_label.config(text=filename[:22] + '...' + filename[-10:])

    btn.grid(column=2)
    file_label.grid(column=1, row=row, sticky='w', padx=(10, 0), pady=(20, 0))


def write_files(feed: Feed, posts_file: str, fields: List[Field], write_comments: Optional[str], image_dir,
                from_date: datetime, to_date: datetime):
    print('Initializing...')
    posts_file = open(posts_file, 'w+', encoding='utf-8', newline='')
    comments_file = open(write_comments, 'w+', encoding='utf-8', newline='') if write_comments else None
    try:
        posts_writer = csv.writer(posts_file, quoting=csv.QUOTE_ALL)
        posts_writer.writerow(Post.CSV_COLUMNS)
        if write_comments:
            comments_writer = csv.writer(comments_file, quoting=csv.QUOTE_ALL)
            comments_writer.writerow(Comment.CSV_COLUMNS)

        past_date_count = 0
        for post in feed.browse(fields=fields, image_dir=image_dir):
            if post.metadata.timestamp is not None:
                if post.metadata.timestamp > to_date:
                    continue
                if isinstance(feed, PageFeed) and post.metadata.timestamp < from_date:
                    break
                elif isinstance(feed, GroupFeed) and post.metadata.timestamp < from_date:
                    past_date_count += 1
                if past_date_count >= 10:
                    break

            posts_writer.writerow(post.csv)
            if write_comments:
                for comment in post.comments:
                    comments_writer.writerow(comment.csv)
    finally:
        posts_file.close()
        if comments_file:
            comments_file.close()


def start(url: str, fields: List[Field], email, password, post_file: str, comments_file: str, image_dir: str,
          from_date: datetime, to_date: datetime):
    if url.startswith('https://www.facebook.com/groups'):
        feed = GroupFeed(email, password, url)
    else:
        feed = PageFeed(email, password, url)

    write_files(feed, post_file, fields, comments_file, image_dir, from_date, to_date)


if __name__ == '__main__':

    root = ThemedTk(theme='clam')
    root.title('Facebook Scraper')
    # root.resizable(False, False)
    root.geometry('600x800')

    try:
        # call a dummy dialog with an impossible option to initialize the file
        # dialog without really getting a dialog window; this will throw a
        # TclError, so we need a try...except :
        try:
            root.tk.call('tk_getOpenFile', '-foobarbaz')
        except tk.TclError:
            pass
        # now set the magic variables accordingly
        root.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
        root.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')
    except:
        pass

    # ttk.Style(root).theme_use('alt')
    row_count = 0

    Label(text='Email').grid(column=0, row=row_count, sticky='w', pady=(20, 0), padx=(20, 0))
    email_box = Entry()
    email_box.grid(column=1, row=row_count, sticky='e', padx=(10, 0), pady=(20, 0))
    row_count += 1

    Label(text='password').grid(column=0, row=row_count, sticky='w', pady=(20, 0), padx=(20, 0))
    password_box = Entry(show='*')
    password_box.grid(column=1, row=row_count, sticky='e', padx=(10, 0), pady=(20, 0))
    row_count += 1

    Label(text='URL').grid(column=0, row=row_count, sticky='w', pady=(20, 0), padx=(20, 0))
    url_box = Entry()
    url_box.grid(column=1, row=row_count, sticky='e', padx=(10, 0), pady=(20, 0))
    row_count += 1

    Label(text='From Date').grid(column=0, row=row_count, sticky='w', pady=(20, 0), padx=(20, 0))
    from_picker = Entry()
    from_picker.grid(column=1, row=row_count, sticky='e', padx=(10, 0), pady=(20, 0))
    hint(from_picker, 'dd/mm/yyyy')
    row_count += 1

    Label(text='To Date').grid(column=0, row=row_count, sticky='w', pady=(20, 0), padx=(20, 0))
    to_picker = Entry()
    to_picker.grid(column=1, row=row_count, sticky='e', padx=(10, 0), pady=(20, 0))
    hint(to_picker, 'dd/mm/yyyy')
    row_count += 1

    save_file_row = row_count  # Need to pass in lambda so keep as different var
    save_file_label = Label(text='File to save:')
    save_file_label.grid(column=0, row=row_count, sticky='w', padx=(20, 0), pady=(20, 0))
    save_file_var = tk.StringVar()
    save_file_btn = Button(text='Set', command=lambda: file_picker_cmd(save_file_btn, save_file_row, save_file_var))
    save_file_btn.grid(column=1, row=row_count, sticky='w', padx=(10, 0), pady=(20, 0))
    row_count += 1

    Label(text='Fields').grid(column=0, row=row_count, sticky='w', padx=(10, 0), pady=(20, 0))
    row_count += 1

    field_btns = {}
    column = 0
    for field in Field:

        if field in [Field.RECOMMENDED, Field.SPONSORED, Field.LIKED]:
            continue

        c = Checkbutton(text=field.value)
        if field != Field.COMMENT_TREE:
            c.state(['!alternate', 'selected'])
        c.grid(column=column, row=row_count, sticky='w', padx=(10, 0))
        if field == Field.IMAGE:
            pass
        field_btns[field] = c

        if column == 2:
            row_count += 1
            column = 0
        else:
            column += 1
    row_count += 1

    img_dir_label = Label(text='Image Directory:')
    img_dir_btn = Button(text='Set')
    img_dir_pick_label = Label()
    img_dir_var = tk.StringVar()
    img_row = row_count * 1


    def image_cmd():
        if field_btns[Field.IMAGE].instate(['selected']):
            img_dir_label.grid(column=0, row=img_row, sticky='w', padx=(20, 0), pady=(20, 0))
            img_dir_btn.config(command=lambda: file_picker_cmd(img_dir_btn, img_row, img_dir_var,
                                                               file_label=img_dir_pick_label, directory=True))
            img_dir_btn.grid(column=1, row=img_row, sticky='w', padx=(20, 0), pady=(20, 0))
        else:
            img_dir_label.grid_forget()
            img_dir_btn.grid_forget()
            img_dir_pick_label.grid_forget()
            img_dir_var.set('')


    field_btns[Field.IMAGE].config(command=image_cmd)
    field_btns[Field.IMAGE].state(['!alternate'])
    row_count += 1

    comment_file_label = Label(text='Comments file:')
    comment_file_btn = Button(text='Set')
    comment_file_pick_label = Label()
    comment_file_var = tk.StringVar()
    comment_file_row = row_count


    def comments_cmd():
        if field_btns[Field.COMMENT_TREE].instate(['selected']):
            comment_file_label.grid(column=0, row=comment_file_row, sticky='w', padx=(20, 0), pady=(20, 0))
            comment_file_btn.config(
                command=lambda: file_picker_cmd(comment_file_btn, comment_file_row, comment_file_var,
                                                file_label=comment_file_pick_label))
            comment_file_btn.grid(column=1, row=comment_file_row, sticky='w', padx=(20, 0), pady=(20, 0))
        else:
            comment_file_label.grid_forget()
            comment_file_btn.grid_forget()
            comment_file_pick_label.grid_forget()
            comment_file_var.set('')


    field_btns[Field.COMMENT_TREE].config(command=comments_cmd)
    field_btns[Field.COMMENT_TREE].state(['!alternate'])
    row_count += 1

    image_cmd()
    comments_cmd()

    start_btn = Button(text='Start!')
    start_btn.grid(row=row_count, column=0, sticky='w', padx=(10, 0), pady=(40, 0))
    row_count += 1


    def start_cmd():
        fields = [field for field, btn in field_btns.items() if btn.instate(['selected'])]
        email = email_box.get()
        if not validators.email(email):
            showerror('Error', 'Invalid email')
            return

        passowrd = password_box.get()
        if not passowrd:
            showerror('Error', 'Please insert password')
            return

        url = url_box.get()
        if not url.startswith('https://www.facebook.com'):
            showerror('Error', 'Invalid URL. Must be either a facebook page or a facebook group.')
            return

        try:
            from_date = datetime.strptime(from_picker.get(), '%d/%m/%Y')
        except ValueError:
            showerror('Error', 'Invalid start date. Date format should be dd/mm/yy')
            return

        try:
            to_date = datetime.strptime(to_picker.get(), '%d/%m/%Y')
        except ValueError:
            showerror('Error', 'Invalid end date. Date format should be dd/mm/yy')
            return

        post_file = save_file_var.get()
        if not post_file:
            showerror('Error', 'Please set a save file')
            return

        image_dir = img_dir_var.get()
        if not image_dir and Field.IMAGE in fields:
            showerror('Error', 'Please set image directory')
            return

        comments_file = comment_file_var.get()
        if not comments_file and Field.COMMENT_TREE in fields:
            showerror('Error', 'Please set comments file')
            return

        start(url, fields, email, passowrd, post_file, comments_file, image_dir, from_date, to_date)


    start_btn.config(command=start_cmd)

    # log_box = Label(text='test')
    # def stdout_decor(func):
    #     def inner(stdout):
    #         try:
    #             text: str = log_box.cget('text')
    #             text += '\n' + stdout
    #             if len(text.splitlines()) > 5:
    #                 text = '\n'.join(text.splitlines()[1:])
    #             log_box.config(text=text)
    #             return func(stdout)
    #         except:
    #             return func(stdout)
    #
    #     return inner
    # sys.stdout.write = stdout_decor(sys.stdout.write)
    # log_box.grid(row=row_count, column=0, sticky='w', padx=(10, 0), pady=(40, 0))

    root.mainloop()
