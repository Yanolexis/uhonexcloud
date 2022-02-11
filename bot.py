import os
import os.path as osp
import re
import argparse
import shutil
import sys
import tempfile
import six
import random
import time
import requests
import telegram
import youtube_dl
import YouTube
import tqdm
import multiFile
import zipfile
from tqdm.utils import CallbackIOWrapper
from pathlib import Path
from tqdm.contrib.telegram import tqdm
from zipfile import ZipFile
from mega import Mega
from YouTube import YouTube
from telegram import Bot, File, Update
from telegram.ext import (
    Updater,
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

TIMEOUT: float = 60
CHUNK_SIZE = 1024
mega = Mega()
m = mega
yt = YouTube()

class NextcloudBOT:

    def __init__(self):
        self._admin  = [838548810,1102848585]
        self._admins = [838548810,1102848585]
        self._token_bot = os.environ["BOT"]
        self._user = os.environ["USER"]
        self._password = os.environ["PASSWD"]
        self.email = os.environ["EMAIL"]
        self.password = os.environ["PASS"]
        self._job = 0
        self._file_ids = {}
        self._num_id = 0
        self._goo_drive_1 = 0
        self._goo_drive_2 = 0
        self._send_size = 0
        self._archive_upload = 0
        self._user_final = ""
        self._request = requests.Session()
        self._request.auth = (self._user, self._password)
        self._obj = Bot(token=self._token_bot)
        self._updater = Updater(token=self._token_bot, use_context=True)
        self._dispatcher = self._updater.dispatcher
        self._handlers = [CommandHandler('start', self.start),
                          CommandHandler('status', self.status),
                          MessageHandler(Filters.text, self.text_filter, run_async=True)]
        self._header = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'Accept': 'application/json, text/plain, */*',
            'requesttoken': '',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4389.90 Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://nube.uho.edu.cu/',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        }

    def prepare(self):
        for handler in self._handlers:
            self._dispatcher.add_handler(handler)

    def run(self):
        self.prepare()
        self._updater.start_polling()
        self._obj.send_message(chat_id=self._admin[0], text='BOT ACTIVO :)', reply_markup={'remove_keyboard': True})
        self._updater.idle()

    def start(self, update: Update, context: CallbackContext):
        print(f'{update.effective_user.name} --> {update.message.text}')
        if not int(update.effective_user.id) in self._admins:
            return
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Bienvenido {}'.format(update.effective_user.name),
                                     reply_to_message_id=update.message.message_id)

    def status(self, update: Update, context: CallbackContext):
        if not int(update.effective_user.id) in self._admins:
            return
        else:
            uso = "NO"
            if self._job != 0:
                uso = "SI"
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="<b>ESTADISTICAS DE USO\n\nEN USO: {}\nTAREAS ACTUALES: {}\nARCHIVOS SUBIDOS: {}\nTOTAL DE MB: {}MB</b>".format(
                                         uso,
                                         str(self._job),
                                         self._archive_upload,
                                         round(self._send_size / 1024 / 1024, 2),
                                     ),
                                     parse_mode=telegram.ParseMode.HTML)

    def text_filter(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        cola = 0
        print('{} --> {}'.format(update.effective_user.name, update.message.text))
        if not int(update.effective_user.id) in self._admins:
            return
        
        if update.message.text.startswith('/acc'):
            if not int(update.effective_user.id) in self._admin:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>No tienes acceso para usar este comando {}!</b>'.format(update.effective_user.name),
                                     reply_to_message_id=update.message.message_id, parse_mode=telegram.ParseMode.HTML)
                return
            text = update.message.text
            id = text.replace('/acc ','')
            print(id)
            self._admins.append(int(id))
            context.bot.send_message(chat_id=id,
                                     text='Ya tienes acceso al bot!')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>El Usuario {} tiene acceso al bot! \nLista de usuarios con acceso:\n{}</b>'.format(str(id),str(self._admins)),
                                     reply_to_message_id=update.message.message_id, parse_mode=telegram.ParseMode.HTML)
            return

        if update.message.text.startswith('/ban'):
            if not int(update.effective_user.id) in self._admin:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>No tienes acceso para usar este comando {}!</b>'.format(update.effective_user.name),
                                     reply_to_message_id=update.message.message_id, parse_mode=telegram.ParseMode.HTML)
                return
            text = update.message.text
            id = text.replace('/ban ','')
            print(id)
            self._admins.remove(int(id))
            context.bot.send_message(chat_id=id,
                                     text='Has sido baneado del bot!')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>El Usuario {} no tiene acceso al bot! \nLista de usuarios con acceso:\n{}</b>'.format(str(id),str(self._admins)),
                                     reply_to_message_id=update.message.message_id, parse_mode=telegram.ParseMode.HTML)
            
            return                       
        if update.message.text.startswith('/kill'):

            try:
                msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text="<b>Eliminando archivo...</b>",
                                               parse_mode=telegram.ParseMode.HTML)
                message = update.message.text
                file_name = message[6:]
                url = "https://nube.uho.edu.cu//remote.php/webdav/{}".format(file_name)
                con_del = self._request.delete(url=url)
                print(con_del.status_code)

                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivo {} eliminado!</b>'.format(file_name),
                                              parse_mode=telegram.ParseMode.HTML
                                              )
                return
            except Exception as error:
                print(error)
                update.message.reply_text(text="Error al eliminar el archivo.\n\n{}".format(str(error)))
                return

        if update.message.text.startswith('/delete_ID'):

            try:
                message = update.message.text
                id_file = int(message[11:])
                list_dic = self._file_ids[id_file]
                url = list_dic[0]
                name_file = list_dic[1]
                con_del = self._request.delete(url=url)
                print(con_del.status_code)
                update.message.reply_text(text="Archivo {} eliminado!".format(name_file))
                return
            except Exception as error:
                print(error)
                update.message.reply_text(text="Ocurrio un error al eliminar el archivo.\n\n{}".format(str(error)))
                return

        if update.message.text.startswith('/storage'):
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Obteniendo datos...',
                                     reply_to_message_id=update.message.message_id)
            m.login(self.email, self.password)
            print('Sesión iniciada!')
            spacem = m.get_storage_space()
            print(spacem)
            used = round(spacem['used']/1024/1024/1024,2)
            total = round(spacem['total']/1024/1024/1024,2)
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>La cuenta {} tiene usado {} GiB de {} GiB</b>'.format(str(self.email),str(used),str(total)),
                                              parse_mode=telegram.ParseMode.HTML)
            return

        if update.message.text.startswith('/del'):
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Eliminando...',
                                     reply_to_message_id=update.message.message_id)
            message = update.message.text
            url = message.replace('/del','')
            try:
                m.login(self.email, self.password)
                print('Sesión iniciada!')
                delurl = m.delete_url(url)
                print(delurl)
                empty = m.empty_trash()
                print(empty)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivo eliminado de mega!!</b>',
                                              parse_mode=telegram.ParseMode.HTML)
            except Exception as x: print(x)
            return

        if update.message.text.startswith('/up'):
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Procesando...',
                                     reply_to_message_id=update.message.message_id)
            self._job += 1
            message = update.message.text
            multiFile.clear()
            url = message.replace('/up ','')
            print('Descargando '+str(url))
            resp = requests.get(url=url, stream=True)
            file = self.filename_geturl(url, resp)
            if file[0] == 'heroku' or file[0] == 'direct':
                    file = file[1]
                    file = self.clean_name(file)
                    self.url_down(url, file, update, context, msg)
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Iniciando sesión en mega...</b>',
                                              parse_mode=telegram.ParseMode.HTML)
            chunk_size = 1024 * 1024 * 5000
            mult_file =  multiFile.MultiFile(file+'.7z',chunk_size)
            zip = ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            zip.write(file)
            zip.close()
            mult_file.close()
            link = ''
            try: 
                m.login(self.email, self.password)
                print('Sesión iniciada!')
                for f in multiFile.files:
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                                  text='<b>Subiendo {} a mega...</b>'.format(f),
                                                  parse_mode=telegram.ParseMode.HTML)
                    m.upload(f)
                    link += str(f)+'\n'+m.export(f)+'\n'
                    os.unlink(file)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivos subidos \nLinks: \n{}</b>'.format(link),
                                              parse_mode=telegram.ParseMode.HTML)
                self._job -= 1
            except Exception as y: 
                print(y)
                self._job -= 1
            return

        if update.message.text.startswith('/dt'):
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Procesando torrent...',
                                     reply_to_message_id=update.message.message_id)
            self._job += 1
            text = update.message.text
           # magnet_link = text.replace('/dt ','')
            try:
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando archivo de magnet...</b>',
                                              parse_mode=telegram.ParseMode.HTML)
                #file = qb.download_from_link(magnet_link)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivo {}\nDescargado con Exito!</b>'.format(file),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Subiendo {} a la nube...</b>'.format(file),
                                              parse_mode=telegram.ParseMode.HTML)
                self.upload_file(file)
                link = self.get_share_link(file)
                self._num_id += 1
                self._file_ids[self._num_id] = ["https://nube.uho.edu.cu//remote.php/webdav/{}".format(file),
                                                "{}".format(file)
                                                ]
                
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Archivo {} subido!\nLink de descarga: {}\n\n/delete_ID_{}'.format(str(file), str(link), str(self._num_id)),
                                         reply_to_message_id=update.message.message_id)
                self._archive_upload += 1
                self._job -= 1
                return
            except Exception as g: 
                print(g)
                self._job -= 1
                return

        if '/drive' in update.message.text:
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Procesando enlace de google drive...',
                                           reply_to_message_id=update.message.message_id)
            text = update.message.text
            text = text.replace('/drive ','')
            print(str(text))
            file_id = str(text[5:])
            print(file_id)
            destination = str(text[:4])
            print(destination)
            try:
                self._job += 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando archivo...</b>',
                                              parse_mode=telegram.ParseMode.HTML)
                file = self.download_file_from_google_drive(file_id, destination)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivo {}\nDescargado con Exito!</b>'.format(file),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Subiendo {} a la nube...</b>'.format(file),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                self.upload_file(file, chat_id)
                link = self.get_share_link(file)
                self._num_id += 1
                self._file_ids[self._num_id] = ["https://nube.uho.edu.cu//remote.php/webdav/{}".format(file),
                                                "{}".format(file)
                                                ]
                
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Archivo {} subido!\nLink de descarga: {}\n\n/delete_ID_{}'.format(str(file), str(link), str(self._num_id)),
                                         reply_to_message_id=update.message.message_id)
                self._archive_upload += 1
                self._job -= 1

            except Exception as r:
                self._job -= 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>{r}</b>',
                                              parse_mode=telegram.ParseMode.HTML)
                print(r)
            return

        if not update.message.text.startswith('http'):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='{} envia un enlace válido!'.format(update.effective_user.name),
                                     reply_to_message_id=update.message.message_id)

            return

        if self._job != 0:
            cola = context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>Enlace en cola...</b>',
                                     reply_to_message_id=update.message.message_id, parse_mode=telegram.ParseMode.HTML)
        if cola != 0:
             context.bot.delete_message(chat_id=update.effective_chat.id, message_id=cola.message_id)
            
        if 'youtu' in update.message.text:
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Procesando link de youtube...',
                                           reply_to_message_id=update.message.message_id)
            url = update.message.text
            try:
                self._job += 1
                inicio = time.time()
                result = yt.get_youtube_info(url)
                if 'entries' in result:
                    #Playlist
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>No puedo procesar playlist!</b>',
                                              parse_mode=telegram.ParseMode.HTML)
                
                else:
                    #Video
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando video...</b>',
                                              parse_mode=telegram.ParseMode.HTML)
                    formats = yt.filter_formats(result['formats'])
                    format = formats[-1]
                    videofile = result['title']+ '.mp4'
                    videofile = str(videofile).replace('*','')
                    req = self._request.get(format['url'], stream = True,allow_redirects=True)
                    total = int(req.headers["Content-Length"])
                    self._send_size += total
                    print(str(total))
                    if req.status_code == 200:
                        file_wr = open(videofile,'wb')
                        chunk_por = 0
                        for chunk in req.iter_content(chunk_size = 1024 * 1024 * 1):
                                if chunk:
                                    chunk_por += len(chunk)
                                    pct = chunk_por / total * 100
                                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando {}%\nDescargado: {} MiB\nTotal: {} MiB</b>'.format(round(float(pct), 2),round(chunk_por / 1024 / 1024, 2), round(total / 1024 /1024,2)),
                                              parse_mode=telegram.ParseMode.HTML)
                                    file_wr.write(chunk)
                        file_wr.close()
                        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Subiendo {} a la nube...</b>'.format(str(videofile)),
                                              parse_mode=telegram.ParseMode.HTML)
                        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                        self.upload_file(videofile, chat_id)
                        link = self.get_share_link(videofile)
                        self._num_id += 1
                        self._file_ids[self._num_id] = ["https://nube.uho.edu.cu//remote.php/webdav/{}".format(videofile),
                                                "{}".format(videofile)
                                                ]
                        fin = time.time()
                        tiempo = round(fin-inicio,0)
                        tiempo = time.strftime("%H:%M:%S", time.gmtime(tiempo))
                        
                        context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text='Archivo {} subido!\nLink de descarga: {}\nTarea Completada en: {} \n\n/delete_ID_{}'.format(
                                                 videofile, link, str(tiempo), str(self._num_id)),
                                                 reply_to_message_id=update.message.message_id)
                        self._archive_upload += 1

                    else:
                        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Error al descargar video!</b>',
                                              parse_mode=telegram.ParseMode.HTML)

                self._job -= 1
            except Exception as ex:
                self._job -= 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Error!! {}</b>'.format(str(ex)),
                                              parse_mode=telegram.ParseMode.HTML)
            return
                
        if 'mediafire' in update.message.text:
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Procesando link de mediafire...',
                                           reply_to_message_id=update.message.message_id)
            url = update.message.text
            output = None
            quiet=False
            try:
                self._job += 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando archivo de {}...</b>'.format(url),
                                              parse_mode=telegram.ParseMode.HTML)
                file = self.download(url, output, quiet)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivo {}\nDescargado con Exito!</b>'.format(file),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Subiendo {} a la nube...</b>'.format(file),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                self.upload_file(file, chat_id)
                link = self.get_share_link(file)
                self._num_id += 1
                self._file_ids[self._num_id] = ["https://nube.uho.edu.cu//remote.php/webdav/{}".format(file),
                                                "{}".format(file)
                                                ]
                
                
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Archivo {} subido!\nLink de descarga: {}\n\n/delete_ID_{}'.format(str(file), str(link), str(self._num_id)),
                                         reply_to_message_id=update.message.message_id)
                self._archive_upload += 1
                self._job -= 1
            except Exception as k:
                self._job -= 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Error!! {}</b>'.format(str(k)),
                                              parse_mode=telegram.ParseMode.HTML)
            return
            
        if 'mega' in update.message.text:
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Procesando link de mega...',
                                           reply_to_message_id=update.message.message_id)
            url = update.message.text
            try:
                self._job += 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando archivo de {}...</b>'.format(url),
                                              parse_mode=telegram.ParseMode.HTML)
                magapylol = m.download_url(url)
                req = self._request.get(url, stream=True)
                total = int(req.headers["Content-Length"])
                self._send_size += total
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Archivo {}\nDescargado con Exito!</b>'.format(magapylol),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Subiendo {} a la nube...</b>'.format(magapylol),
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                self.upload_file(magapylol, chat_id)
                link = self.get_share_link(magapylol)
                self._num_id += 1
                self._file_ids[self._num_id] = ["https://nube.uho.edu.cu//remote.php/webdav/{}".format(magapylol),
                                                "{}".format(magapylol)
                                                ]
                
                
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Archivo {} subido!\nLink de descarga: {}\n\n/delete_ID_{}'.format(str(magapylol), str(link), str(self._num_id)),
                                         reply_to_message_id=update.message.message_id)
                self._archive_upload += 1
                self._job -= 1
                return
            except Exception as f:
                self._job -= 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Error!! {}</b>'.format(str(f)),
                                              parse_mode=telegram.ParseMode.HTML)

        else:
            message = update.message.text
            msg = context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Enlace detectado...</b>",
                                           parse_mode=telegram.ParseMode.HTML)

            try:
                self._job += 1
                inicio = time.time()
                resp = requests.get(url=message, stream=True)
                full_name = self.filename_geturl(message, resp)
                print(full_name)
                if full_name[0] == 'heroku' or full_name[0] == 'direct':
                    full_name = full_name[1]
                    full_name = self.clean_name(full_name)
                    self.url_down(message, full_name, update, context, msg)
                else: pass
                
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Subiendo archivo a la nube...</b>',
                                              parse_mode=telegram.ParseMode.HTML)
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                self.upload_file(full_name, chat_id)
                link = self.get_share_link(full_name)
                self._num_id += 1
                self._file_ids[self._num_id] = ["https://nube.uho.edu.cu//remote.php/webdav/{}".format(full_name),
                                                "{}".format(full_name)
                                                ]
                fin = time.time()
                tiempo = round(fin-inicio,0)
                tiempo = time.strftime("%H:%M:%S", time.gmtime(tiempo))
                
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Archivo {} subido!\nLink de descarga: {}\nTarea Completada en: {} \n\n/delete_ID_{}'.format(
                                             full_name, link, str(tiempo), str(self._num_id)),
                                         reply_to_message_id=update.message.message_id)
                self._archive_upload += 1
                self._job -= 1

            except Exception as er:
                self._job -= 1
                print(er)
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='{}'.format(er))

    def upload_file(self, file, chat_id):
        filename_path = Path(f"{file}")
        print("Func. upload_file")
        with requests.Session() as request:
            request.auth = (self._user, self._password)
            size = filename_path.stat().st_size if filename_path.exists() else 0
            print(size)
            with tqdm(token=self._token_bot,
                      chat_id=chat_id,
                      total=size,
                      desc="Subiendo... ",
                      mininterval=3.0,
                      unit="B",
                      unit_scale=True,
                      bar_format="{desc}{percentage:3.0f}% / {rate_fmt}{postfix}",
                      unit_divisor=CHUNK_SIZE,
                      ) as t, open(filename_path, "rb") as fileobj:
                wrapped_file = CallbackIOWrapper(t.update, fileobj, "read")
                with request.put(
                        url="https://nube.uho.edu.cu//remote.php/webdav/{}".format(file),
                        data=wrapped_file,  # type: ignore
                        headers=self._header,
                        timeout=TIMEOUT,
                        stream=True,
                ) as resp:
                    print(resp.status_code)
                    resp.raise_for_status()
                    t.tgio.delete()
                    print("UPLOAD OK!")

    def get_share_link(self, filename):
        with requests.Session() as request:
            request.auth = (self._user, self._password)
            response = request.get('https://nube.uho.edu.cu//index.php/apps/dashboard/')
            i = response.content.index(b'token=')
            tok = str(response.content[i + 7:i + 96])[2:-1]
            self._header.update({'requesttoken': tok})
            data = '{"path":"' + f'/{filename}' + '","shareType":3, "password":"' + f'QweRty@0909' + '"}'
            response = request.post('https://nube.uho.edu.cu//ocs/v2.php/apps/files_sharing/api/v1/shares',
                                headers=self._header, cookies=response.cookies, data=data)
            url = response.json()
        try:
            url = url['ocs']['data']['url']
        except Exception as e:
            print(f'Error getting share link: {e}')
            url = "Error: {}".format(e)
        return url

    def filename_geturl(self, url, resp):

        if url.find("heroku") != -1:
            print("heroku")
            return self.get_heroku_bot(resp, url)
        elif url.find("mega") != -1:
            return ["none"]
        else:
            file = url.split("/", -1)[-1]
            if file.find("?") != -1:
                file = file.split("?", -1)[0]
            if file.find(".") == -1:
                try:
                    file = resp.headers["Content-Disposition"].split("", 1)[1].split("=", 1)[1][1:-1]
                except Exception as err:
                    print(err)
                    if url.find("checker") != -1:
                        file += ".mp4"
                    else:
                        file += ".ext"
            return ["direct", file]

    @staticmethod
    def get_heroku_bot(resp, url):
        print(resp.headers)
        try:
            file = resp.headers["Conetnt-Disposition"].split(" ", 1)[1].split("=", 1)[1][1:-1]
        except Exception as err:
            print(err)
            try:
                # ext = resp.headers["Content-Type"]
                # file = "heroku_file.{}".format(ext.split("/", -1)[1])
                file_name = url.split("/")
                file = file_name[-1]
            except Exception as error:
                print(error)
                file = "defaul_name.ext"
        return ["heroku", file]

    @staticmethod
    def clean_name(full_name):
        full_name = full_name.replace(" ", "_")
        full_name = full_name.replace("%20", "_")
        full_name = full_name.replace("(", "")
        full_name = full_name.replace(")", "")
        full_name = full_name.replace("$", "")
        full_name = full_name.replace("%", "_")
        return full_name
    
    def extractDownloadLink(self, contents):
        for line in contents.splitlines():
            m = re.search(r'href="((http|https)://download[^"]+)', line)
            if m:
                return m.groups()[0]

    def download_file_from_google_drive(self, id, destination):
        URL = "https://docs.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(URL, params = { 'id' : id }, stream = True)
        token = self.get_confirm_token(response)
        if token:
            params = { 'id' : id, 'confirm' : token }
            response = session.get(URL, params = params, stream = True)
        with open(destination, "wb") as f:
            #total = int(req.headers["Content-Length"])
            #self._send_size += total
            chunk_por = 0
            for chunk in response.iter_content(32768):
                if chunk:
                    #chunk_por += len(chunk)
                    #print('Descargado '+str(round(chunk_por/1024/1024,2))+' MiB')
                    f.write(chunk)
                #f.closed()
            return destination
            

    def get_confirm_token(self, response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def download(self, url, output, quiet):
        url_origin = url
        sess = requests.session()

        while True:
            res = sess.get(url, stream=True)
            if 'Content-Disposition' in res.headers:
                # This is the file
                break

            # Need to redirect with confiramtion
            url = self.extractDownloadLink(res.text)

            if url is None:
                print('Permission denied: %s' % url_origin, file=sys.stderr)
                print(
                    "Maybe you need to change permission over "
                    "'Anyone with the link'?",
                    file=sys.stderr,
                )
                return

        if output is None:
            m = re.search(
               'filename="(.*)"', res.headers['Content-Disposition']
           )
            output = m.groups()[0]
            # output = osp.basename(url)

        output_is_path = isinstance(output, six.string_types)

        if not quiet:
            print('Downloading...', file=sys.stderr)
            print('From:', url_origin, file=sys.stderr)
            print(
                'To:',
                osp.abspath(output) if output_is_path else output,
                file=sys.stderr,
            )

        if output_is_path:
            tmp_file = tempfile.mktemp(
                suffix=tempfile.template,
                prefix=osp.basename(output),
                dir=osp.dirname(output),
            )
            f = open(tmp_file, 'wb')
        else:
            tmp_file = None
            f = output

        try:
            total = res.headers.get('Content-Length')
            if total is not None:
                total = int(total)
            for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
            self._send_size += total
            if tmp_file:
                f.close()
                shutil.move(tmp_file, output)
        except IOError as e:
            print(e, file=sys.stderr)
            return
        finally:
            try:
                if tmp_file:
                    os.remove(tmp_file)
            except OSError:
                pass
        return output

    def url_down(self, url, file, update, context, msg):

        try:
            print("Se esta descargando {}".format(file))
            req = self._request.get(url, stream=True)
            total = int(req.headers["Content-Length"])
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                          text="<b>Preparando para descargar...</b>",
                                          parse_mode=telegram.ParseMode.HTML)

            with open(file, "wb") as file_down:
                chunk_por = 0
                mb = 0
                #count = 0
                chunkrandom = random.randint(10.00,30.00)
                inicio = time.time()
                for chunk in req.iter_content(chunk_size= 1024 * 1024 * chunkrandom):
                    chunk_por += len(chunk)
                    mb += len(chunk)
                    porcent = round(float(chunk_por / total * 100), 2)
                    make_text = str(porcent) + '% / 100%'
                    index_make = 1
                    make_text += '\n['
                    while(index_make<21):
                        if porcent >= index_make * 5:
                            make_text+='█'
                        else: 
                            make_text+='░'
                        index_make+=1
                    make_text += ']'
                    fin = time.time()
                    tiempo = round(float(fin-inicio), 2)
                    speed = len(chunk) / tiempo
                    parte = round(float(total - chunk_por), 2)
                    faltan = round(parte / speed, 2)
                    faltan = time.strftime("%M.%S", time.gmtime(faltan))
                    faltan = round(float(faltan), 2)
                    inicio = 0
                    inicio = time.time()
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                                  text="<b>Descargando {}...\n\nProgreso:{}\nVelocidad: {} MiB/s\nDescargado: {}MB\nTotal: {}MB\nFaltan: {} Minutos Aprox</b>".format(
                                                      str(file),
                                                      str(make_text),
                                                      round(speed / 1024 / 1024, 2),
                                                      round(mb / 1024 / 1024, 2),
                                                      round(total / 1024 / 1024, 2),
                                                      round(float(faltan), 2)),
                                                  parse_mode=telegram.ParseMode.HTML)
                    file_down.write(chunk)

            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                          text="<b>Descargado y guardado correctamente!</b>",
                                          parse_mode=telegram.ParseMode.HTML)
            self._send_size += total
            print("Termino de descargar!")
        except Exception as e:
            print(e)
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                          text="<b>Ocurrio un error a la hora de descargar!</b>",
                                          parse_mode=telegram.ParseMode.HTML)

    @staticmethod
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    @staticmethod
    def save_response_content(response, destination, update, context, msg):
        CHUNK_SIZE = 32768

        with open(destination, "wb") as f:
            count = 0
            for chunk in response.iter_content(CHUNK_SIZE):
                count += 1
                context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id,
                                              text='<b>Descargando{}</b>'.format("." * count),
                                              parse_mode=telegram.ParseMode.HTML)
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    if count == 3:
                        count = 0
                     

class CloudBot:
    __name__: str
    __version__: str

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.__version__ = '0.1'
        self.__name__ = 'bot'

    def run(self):
        self.bot.run()


cloud = NextcloudBOT()
active_bot = CloudBot(cloud)
active_bot.run()
