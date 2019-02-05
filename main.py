#!/usr/bin/env python

import argparse
import csv
import logging
import os
import sys
import time

import requests
from requests.auth import HTTPBasicAuth

from slugify import slugify


class ExceptionBoleto(Exception):
    """Exeptions Boleto."""
    pass


URL = "https://app.boletocloud.com/api/v1/%s"
SLEEP = 2
DEFAULT_AGENT = "boleto-lions v0.1"

logger = logging.getLogger('boleto_lions')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


def save_pdf(filename, content):
    """salva os arquivos pdf."""
    logger.info("Save: %s" % filename)
    try:
        with open(os.path.join("./boletos/", slugify(filename) + ".pdf"), "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error("falha ao salvar o documento: %s" % e)
        raise ExceptionBoleto("falha ao salvar o boleto: %s" % filename)


def get_boleto(token_auth, token_boleto, timeout=5):
    """obtem o boleto atraves do token gerado pelo boleto.cloud."""
    auth = HTTPBasicAuth(token_auth, "token")
    headers = {
        'User-Agent': DEFAULT_AGENT
    }
    try:
        logger.info("Requisitando boleto.cloud para o token: %s" %
                    token_boleto)
        r = requests.get(
            URL % "boletos/{token}".format(token=token_boleto), auth=auth, timeout=timeout, headers=headers)
    except requests.exceptions.Timeout:
        logging.error(
            "timeout ao conectar no boletos.cloud valor atual: %d segundos" % timeout)
        raise ExceptionBoleto(
            "timeout ao conectar no boletos.cloud")
    if r.status_code != 200:
        logging.error("codigo de status http diferente 200: %s" %
                      str(r.json()))
        raise ExceptionBoleto(
            "falha ao baixar o boleto de token: %s razao: %s" % (token_boleto, str(r.json())))
    return r.content


def open_report(filename, token_auth, timeout):
    """Abre o arquivo CSV formato: token, nome socio"""
    try:
        with open(filename) as f:
            csv_reader = csv.reader(f, delimiter=',')
            line_count = 0
            # Percorremos todas as linhas do arquivo csv
            for row in csv_reader:
                token_boleto = row[0]  # coluna 1
                socio = row[1]  # coluna 2
                if token_boleto == "" or socio == "":
                    raise ExceptionBoleto(
                        "Formato invalido, a linha: %d nao possui token ou socio." % row)
                content_boleto = get_boleto(token_auth, token_boleto, timeout)
                save_pdf(socio, content_boleto)
                line_count += 1
                time.sleep(SLEEP)
    except Exception as e:
        logger.error("falha ao ler o arquivo csv, razao: %s" % e)
        raise ExceptionBoleto("falha ao ler o arquivo: %s" % filename)


def main(args):
    logger.info("Gerando boletos apartir do arquivo: %s" % args.csvfile)
    open_report(args.csvfile, args.token_auth, args.timeout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Gera os boletos do Lions Clube Jaboticabal.')
    parser.add_argument('csvfile', type=str,
                        help='arquivo csv gerado pelo boleto.cloud.')
    parser.add_argument('token', type=str,
                        help='token do boleto.cloud')
    parser.add_argument('--timeout', default=5, type=int,
                        help='valor para o timeout padrao eh 5')
    args = parser.parse_args()
    main(args)
