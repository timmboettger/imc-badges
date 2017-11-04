#!/usr/bin/env python2

import argparse
import csv
import math
import os
import subprocess
import textwrap

class BadgePrinter:

	def __init__(self):
		
		# sizes in mm
		self.badge_width = 85
		self.badge_height= 54
		self.badge_padding = 2

		self.paper_width = 210 # A4 paper

		self.page_leftmargin = 20
		self.page_topmargin = 13

		# duplex printer tend to shift content horizontally when duplexing
		# this offset can be corrected here
		self.printer_leftmargin_offset_flipside = 0

		self.header_height = 18.3

		self.tex_document = ''
		self.badge_counter = 0
		self.backside = []

		self._tex_header = textwrap.dedent(r'''			\documentclass[a4paper]{article}
			\usepackage[a4paper, margin=0pt]{geometry}
			\usepackage[utf8]{inputenc}
			%\usepackage[dvips]{geometry}
			\usepackage[texcoord]{eso-pic}
			\usepackage{picture}
			%\usepackage{parskip}
			\usepackage{graphicx}
			%\usepackage{array}
			\usepackage{xcolor}

			\usepackage[default]{raleway}

			%\setlength{\oddsidemargin}{-15mm}
			\pagestyle{empty}

			\begin{document}
		''')
		
		self._tex_footer = textwrap.dedent(r'''	      \end{document}''')

		self._tex_newpage = textwrap.dedent(r'''			\vspace*{\fill}
			\newpage
		''')

	def tex_header(self):
		self.tex_document += self._tex_header

	def tex_footer(self):
		self.tex_document += self._tex_footer

	def tex_newpage(self):
		self.tex_document += self._tex_newpage
	
	def add_badge(self, position, name, affiliation, flipside=False):
		# left or right badge, x=0 -> left, x=1 -> right
		x = position % 2
		# badge number from top
		y = int(math.ceil((position + 1)/2.0))

		badge_inner_width = self.badge_width - 2*self.badge_padding
		badge_inner_height = self.badge_height - 2*self.badge_padding

		left_margin = self.page_leftmargin + x*self.badge_width
		
		if flipside:
			left_margin = self.paper_width - self.page_leftmargin - 2*self.badge_width + x*self.badge_width + self.printer_leftmargin_offset_flipside

		self.tex_document += textwrap.dedent(r'''			\AddToShipoutPictureBG*{
				%%\put(%smm,%smm){\framebox(%smm,%smm){}}
				\put(%smm,%smm){\framebox(%smm,%smm){}}
				\put(%smm,%smm){\includegraphics[width=81mm,height=50mm]{header.jpg}}
				\put(%smm,%smm){\makebox(%smm,%smm){\parbox{80mm}{\centering{\fontsize{30}{30}\selectfont\textbf{%s}\\\vspace{2mm}\fontsize{12}{12}\selectfont\textit{%s}}}}}
			}
		''' % ( 
			left_margin, -(self.page_topmargin + y*self.badge_height), self.badge_width, self.badge_height,
			left_margin + self.badge_padding, -(self.page_topmargin + y*self.badge_height - self.badge_padding), badge_inner_width, badge_inner_height,
			left_margin + self.badge_padding, -(self.page_topmargin + (y-1)*self.badge_height + self.badge_padding+50),
			left_margin + self.badge_padding, -(self.page_topmargin + y*self.badge_height - self.badge_padding), badge_inner_width, badge_inner_height - self.header_height, name, affiliation)
		)
		
	def next_badge(self, name, affiliation):
		affiliation = affiliation.replace('&', '\\&')
		self.add_badge(self.badge_counter % 10, name, affiliation)

		self.backside.append((name, affiliation))

		self.badge_counter += 1
		
		if self.badge_counter % 10 == 0:
			self.tex_newpage()
			self.flush_backside()

	def flush_backside(self):
		for i in range(len(self.backside)/2):
			tmp = self.backside[2*i]
			self.backside[2*i] = self.backside[2*i+1]
			self.backside[2*i+1] = tmp

		if len(self.backside) % 2:
			self.backside.append(self.backside[-1])
			self.backside[-2] = None

		for i, r in enumerate(self.backside):
			if r is not None:
				self.add_badge(i, r[0], r[1], flipside=True)
		
		self.backside = []
		self.tex_newpage()

	def flush_badges(self):
		if self.backside:
			self.tex_newpage()
			self.flush_backside()

def main(args):
	with open(args.csv_file) as f:
		
		b = BadgePrinter()
		b.tex_header()
		reader = csv.DictReader(f)
		for row in reader:
			if (args.limit and row['Booking Reference'] in args.limit) or not args.limit:
				b.next_badge(row['Delegate Name'], row['1092~Affiliation:'])

	b.flush_badges()
	b.tex_footer()
	
	p = subprocess.Popen(['pdflatex', '-jobname=badges'], stdin=subprocess.PIPE)

	with open('debug.tex', 'w') as f:
		f.write(b.tex_document)

	p.communicate(b.tex_document)

	os.remove('badges.aux')
	os.remove('badges.log')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Create badges for IMC2017.')
	parser.add_argument('csv_file', help='CSV file with input data')
	parser.add_argument('--limit', help='Limit badge generation to specific IDs', nargs='+')

	args = parser.parse_args()

	main(args)
