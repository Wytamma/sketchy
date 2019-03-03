"""
=================================
Access point module for Nanomatch
=================================



"""

import re
import pandas
import random
import delegator

from pathlib import Path
from collections import Counter
from io import StringIO

from colorama import Fore


Y = Fore.YELLOW
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN

LR = Fore.LIGHTRED_EX
LC = Fore.LIGHTCYAN_EX
LB = Fore.LIGHTBLUE_EX
LG = Fore.LIGHTGREEN_EX
LY = Fore.LIGHTYELLOW_EX
LM = Fore.LIGHTMAGENTA_EX


RE = Fore.RESET

from sketchy.minhash import MashSketch


class Sketchy:
    """ Main access interface to Sketchy """

    def __init__(self, survey_result: Path or str = None):




    def create_mash_sketch(
            self,
            prefix: str = 'sketchy',
            data_path: Path or str = Path().home() / 'data.tab',
            kmer_length: int or [int] = 15,

        ):



    def predict_assemblies(
            self,
            assemblies: Path or str,
            sketch: str or Path,
            extension: str = '.fasta'
    ):

        genomes = Path(assemblies).glob(f'*{extension}')

        self._print_header2()
        for i, genome in enumerate(genomes):
            tops = self.dist(genome, sketch, ncpu=16, top=1)
            self._compute_scores(i, tops, genome=genome.name)

    def predict_nanopore(
            self,
            db_path: str or Path,
            read_path: Path or str = None,
            extension='.fq'
    ):
        """ Online predictions on nanopore reads

        :param db_path:
        :param read_path:
        :param extension:
        :return:
        """
        reads = sorted(
            [
                str(
                    read.absolute()
                ) for read in Path(read_path).glob(f'{extension}')
            ], key=natural_key
        )

        self._print_header1()

        lineage = Counter()
        resistance = Counter()
        for i, read in enumerate(reads):
            tops = self.dist(
                read, mashdb=db_path, ncpu=16, top=1
            )
            self._compute_scores(
                i, tops, lineage=lineage, resistance=resistance
            )


    def dist(self, file, mashdb, ncpu=4, top=2):

        result = delegator.run(
            f'mash dist -p {ncpu} {mashdb} {file}'
        )

        df = pandas.read_csv(
            StringIO(result.out), sep='\t', header=None,
            names=[
                "id", 'file', 'dist', "p-value", "shared"
            ], index_col=False
        )

        shared = pandas.DataFrame(
            df.shared.str.split('/').tolist(), columns=['shared', 'total']
        )

        df.shared = shared.shared.astype(int)

        df = df.sort_values(by='shared', ascending=False)

        if top:
            df = df[:top]

        return df

    @staticmethod
    def _print_header1():

        print(
            f"{C}{'-' * 60}{RE}\n"
            f"{LC}{'Read':<5}{RE}",
            f"{LM}{'ST:1':<7}{RE}",
            f"{LC}{'Count':<7}{RE}",
            f"{LY}{'Profile':<12}{RE}",
            f"{LM}{'ST:2':<7}{RE}",
            f"{LY}{'Count':<7}{RE}",
            f"{LY}{'Score':<5}{RE}\n",
            f"{C}{'-' * 60}{RE}"
        )

    @staticmethod
    def _print_header2():

        print(
            f"{C}{'-'*75}{RE}\n"
            f"{LC}{'Genome':<7}{RE}",
            f"{LM}{'Predict':<10}{RE}",
            f"{LY}{'Predict':<12}{RE}",
            f"{LC}{'Hashes':<10}{RE}",
            f"{LM}{'True':<10}{RE}",
            f"{LY}{'True':<12}{RE}",
            f"{LY}{'Diff':<5}{RE}",
            f"\n{C}{'-'*75}{RE}"
        )


    def read_fastq(self, file, fastq: str = None, shuffle: bool = False):

        from Bio import SeqIO
        from datetime import datetime

        dates = []
        ids = []
        lengths = []
        records = {}
        with open(file, "r") as input_handle:
            for record in SeqIO.parse(input_handle, "fastq"):
                time = record.description.split('start_time=')[1]
                time = time.replace('T', '-').strip('Z')
                dtime = datetime.strptime(time, '%Y-%m-%d-%H:%M:%S')
                dates.append(dtime)
                ids.append(record.id)
                lengths.append(len(record.seq))
                records[record.id] = record
                print(record.id, time, len(record.seq))

        df = pandas.DataFrame(
            data={
                'date': dates,
                'read': ids,
                'length': lengths
            }
        ).sort_values(by='date')

        pandas.set_option('display.max_rows', 120)
        df = df.reset_index()

        # 3 percent of genome with large database

        if fastq:

            recs = [
                records[read] for read in df['read']
            ]

            if shuffle:
                recs = random.shuffle(recs)

            with open(fastq, "w") as output_handle:
                SeqIO.write(recs, output_handle, 'fastq')

    def _compute_scores(
            self,
            i: int,
            tops: pandas.DataFrame,
            lineage: Counter = None,
            resistance: Counter = None,
            genome: str = None
    ):

            iids, sts, resist, mashshare = [], [], [], []

            for tid in tops.id:
                iid, st, res = tid.strip('.fasta').split('_')

                if lineage and resistance:
                    lineage.update([st])
                    resistance.update([res])
                else:
                    iids.append(iid)
                    sts.append(st)
                    resist.append(res)
                    mashshare.append(tops[tops['id'] == tid].shared.values[0])

            if lineage and resistance:
                lin = lineage.most_common(3)
                rest = resistance.most_common(3)
                top_st = lin[0][0]
                top_count = lin[0][1]

                try:
                    second_st = lin[1][0]
                    second_count = lin[1][1]
                except IndexError:
                    second_st, second_count = "", ""

                try:
                    # PSG like count score, see Brinda et al. 2019
                    ratio = 2*top_count/(second_count + top_count) - 1
                except TypeError:
                    ratio = ''

                if isinstance(ratio, float):
                    col = f"{RE}" if ratio < 0.6 else f"{G}"
                else:
                    col = f"{RE}"

                print(
                    f"{i:<5}",
                    f"{col}{'ST' + top_st:<7}{RE}",
                    f"{top_count:<7}",
                    f"{self._format_res_string(rest[0][0]):<15}",
                    f"{'ST' + second_st:<7}",
                    f"{second_count:<7}",
                    f"{self._format_score(ratio):<5}"
                )
            else:

                if genome:
                    giid, gst, gres = genome.strip('.fasta').split('_')
                else:
                    giid, gst, gres = '-', '-', '-'

                topst = sts[0]

                diff = self._diff(resist[0], gres)
                print(
                    f"{i:<7}",
                    f"{R if topst != gst else G}{'ST' + topst:<10}{RE}",
                    f"{self._format_res_string(resist[0]):<15}",
                    f"{mashshare[0]:<10}",
                    f"{'ST' + gst:<10}",
                    f"{self._format_res_string(gres):<15}",
                    f"{R if diff > 0 else G}{diff:<7}{RE}",
                )

    @staticmethod
    def _diff(res1, res2):
        """ Equal length strings """
        return sum(1 for x, y in zip(res1, res2) if x != y)

    @staticmethod
    def _format_res_string(rstring: str):

        pretty_rstring = ''
        for r in rstring:
            if r.lower() == 'r':
                pretty_rstring += f'{LR}R'
            else:
                pretty_rstring += f'{LB}S'

        return pretty_rstring + f'{Fore.RESET}'

    @staticmethod
    def _format_score(pstring: str):


        try:
            pfloat = float(pstring)
        except ValueError:
            return pstring

        if pfloat < 0.4:
            col = f'{R}'
        elif 0.4 <= pfloat < 0.6:
            col = f'{Y}'
        else:
            col = f'{G}'

        pfloat = round(pfloat, 5)

        return col + str(pfloat) + f'{Fore.RESET}'



def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]