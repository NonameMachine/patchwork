# Patchwork - automated patch tracking system
# Copyright (C) 2020 Rohit Sarkar <rohitsarkar5398@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import os
import sys

from django.db import transaction
from django.core.management.base import BaseCommand

from patchwork.models import Patch
from patchwork.models import PatchRelation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Parse a relations file generated by PaStA and replace existing'
        'relations with the ones parsed'
    )

    def add_arguments(self, parser):
        parser.add_argument('infile', help='input relations filename')

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])
        if not verbosity:
            level = logging.CRITICAL
        elif verbosity == 1:
            level = logging.ERROR
        elif verbosity == 2:
            level = logging.INFO
        else:
            level = logging.DEBUG

        logger.setLevel(level)

        path = args and args[0] or options['infile']
        if not os.path.exists(path):
            logger.error('Invalid path: %s', path)
            sys.exit(1)

        with open(path, 'r') as f:
            lines = f.readlines()

        # filter out trailing empty lines
        while len(lines) and not lines[-1]:
            lines.pop()

        relations = [line.split(' ') for line in lines]

        with transaction.atomic():
            PatchRelation.objects.all().delete()
            count = len(relations)
            ingested = 0
            logger.info('Parsing %d relations' % count)
            for i, patch_ids in enumerate(relations):
                related_patches = Patch.objects.filter(id__in=patch_ids)

                if len(related_patches) > 1:
                    relation = PatchRelation()
                    relation.save()
                    related_patches.update(related=relation)
                    ingested += 1

                if i % 10 == 0:
                    self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                    self.stdout.flush()

            self.stdout.write('Ingested %d relations' % ingested)