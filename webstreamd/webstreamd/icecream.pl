#!/usr/bin/perl -w 
#
# icecream 1.3
# Copyright (c) 2003-2008 Gil Megidish
#
# Formatted filename patch by Sean Dague (13 Dec 2005)
# Modified by Cristian Greco 2008 (release 1.3)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

use strict; 
use IO::Socket; 
use Getopt::Long;

my $config = {};

my $def_agent = "icecream/1.3";
my $version = "icecream/1.3";
my $accept_header = "audio/mpeg, audio/x-mpegurl, audio/x-scpls, */*";

my $def_timeout = 500;
my $max_sync_count = 3;
my $largest_unknown_buffer = 1024**2;

my @bitrate_table =
(
	[0, 0, 0, 0, 0],
	[32, 32, 32, 32, 8],
	[64, 48, 40, 48, 16],
	[96, 56, 48, 56, 24],
	[128, 64, 56, 64, 32],
	[160, 80, 64, 80, 40],
	[192, 96, 80, 96, 48],
	[224, 112, 96, 112, 56],
	[256, 128, 112, 128, 64],
	[288, 160, 128, 144, 80],
	[320, 192, 160, 160, 96],
	[352, 224, 192, 176, 112],
	[384, 256, 224, 192, 128],
	[416, 320, 256, 224, 144],
	[448, 384, 320, 256, 160],
	[-1, -1, -1, -1, -1, -1]
);

my @freq_table = 
(
	[44100, 22050, 11025],
	[48000, 24000, 12000],
	[32000, 16000, 8000],
	[1, 1, 1, 1]
);

sub check_stop_cond
{
	return if (! defined $config->{'stop-cond'});

	$config->{'stop-cond'} =~ /^(\d+)(\w+)$/;
	
	my $count = $1;
	my $units = $2;
	my $kb = $config->{'bytes-downloaded'} / 1024;

	if ($units eq 'kb') 
	{
		$config->{stop} = ($kb >= $count);
	} 
	elsif ($units eq 'mb') 
	{
		$config->{stop} = ($kb >= ($count * 1024));
	} 
	elsif ($units eq 'min') 
	{
		my $elapsed = (time() - $config->{'start-time'}) / 60;
		$config->{stop} = ($elapsed >= $count);
	} 
	elsif ($units eq 'songs') 
	{
		$config->{stop} = ($config->{'played-tracks'} >= $count);
	} 
	else 
	{
		die "unhandled unit $units\n";
	}
}

sub parse_m3u_playlist
{
	my ($playlist) = shift || return undef;
	my (@lines) = split('\n', $playlist);
	my (@queue) = ();
	my ($id) = 1;

	foreach my $s (@lines) 
	{
		# skip lines beginning with a comment
		if ($s =~ /^#EXT/)
		{
			next;
		}

		my ($entry) = {};
		$entry->{id} = $id++;
		$entry->{file} = $s;
		push @queue, $entry;
	}

	return @queue;
}

sub parse_pls_playlist
{
	my ($playlist) = shift || return undef;
	my (@lines) = split('\n', $playlist);
	my ($line);
	my ($entry, $dirty);
	my ($lastid);
	my (@queue) = ();
	
	# parse_pls_playlist parses a .pls playlist, and
	# returns a vector of all links in content

	$line = shift @lines;
	if (! defined $line || $line !~ /^\[playlist\]/i) 
	{
		# not a valid playlist
		print STDERR "invalid playlist file\n";	
		return undef;
	}

	$entry = {};
	$dirty = 0;

	$lastid = 1;	
	$line = shift @lines;
	while (defined $line) 
	{
		my ($property, $id, $value);
		
		# now expecting FileX, TitleX and LengthX
		if ($line =~ /^(\w+)(\d+)=(.+)$/) 
		{
			$property = $1;
			$id = $2;
			$value = $3;

			$value =~ s/\s*$//s;
			
			if ($id ne $lastid) 
			{
				# different entry
				push @queue, $entry;
				$entry = {};
				$dirty = 0;
				$lastid = $id;
			}
			
			# add property to hash
			$property = lc $property;
			$entry->{$property} = $value;
			$dirty = 1;
		}
		
		$line = shift @lines;
	}
	
	push @queue, $entry if $dirty;
	return @queue;
}

sub slurp_file
{
	my ($filename) = shift || return undef;
	my ($data);
	
	open(SLURPEE, "<$filename") || return undef;
	
	# set delimiter to undef, next read will load the 
	# entire file into memory
	local $/ = undef;
	
	# read entire file
	$data = <SLURPEE>;
	
	close SLURPEE;
	return $data;
}

sub select_socket
{
	my ($handle) = shift || return 0;
	my ($timeout) = shift || return 0;
	my ($v) = '';

	vec($v, fileno($handle), 1) = 1;
	return select($v, $v, $v, $timeout / 1000.0);
}

sub recv_chunk
{
	my ($handle) = shift || return undef;
	my ($cnt) = shift || return undef;
	my ($data) = '';
	
	while ($cnt != 0) 
	{
		my ($chunk, $chunksize);
		my ($next_chunk);
		
		$next_chunk = ($cnt > 0) ? $cnt : 1024;

		if (select_socket($handle, $def_timeout) <= 0) 
		{
			# timed out
			print "Timedout!\n";
			last;
		}
		
		$handle->recv($chunk, $next_chunk);
		$chunksize = length($chunk);		
		if ($chunksize == 0) 
		{
			# error occured, or end of stream
			last;
		}	
		
		$data .= $chunk;
		$cnt -= $chunksize;
		
		# paranoia, what if a bigger chunk is received
		$cnt = 0 unless $cnt > 0;
	}
	
	return $data;
}

sub split_url
{
	my ($url) = shift || return undef;
	my ($host, $port, $path);

	$port = undef;
	
	if ($url =~ /^([\d\w\._\-]+)(:\d+)??(\/.*)??$/) 
	{
		$host = $1;
		if (defined $2) 
		{
			# port includes the colon
			$port = substr($2, 1);
		}
		
		$path = $3;
	} 
	else 
	{
		# unparsable
		print "*** UNPARSABLE ***\n";
		return undef;
	}

	return ($host, $port, $path);	
}

sub slurp_http
{
	my ($location) = shift || return undef;
	my ($host, $port, $path);
	my ($sock);
	my ($data, $request);

	debug("slurping http resource at $location");

	# parse location	
	$location = strip_protocol($location);
	($host, $port, $path) = split_url($location);
		
	# parsing errors?
	return undef unless defined $host;
	$port = 80 unless defined $port;
	$path = "/" unless defined $path;

	debug("retreiving from $host $port $path");

	$sock = IO::Socket::INET->new(PeerAddr => $host,
				PeerPort => $port,
				Proto => 'tcp');
	
	# error connecting?
	return undef unless defined $sock;
	
	$sock->autoflush(1);
	
	my $agent = $config->{'user-agent'};
	$request = "GET $path HTTP/1.0\r\n" .
		"Host: $host:$port\r\n" .
		"Accept: ${accept_header}\r\n" .
		"User-Agent: $agent\r\n" .
		"\r\n";

	debug("sending request to server", $request);
	print $sock $request;

	$data = recv_chunk($sock, -1);
	$sock->shutdown(2);

	debug("data retreived from server", $data);
	return $data;
}

sub get_http_body
{
	my ($message) = shift || return undef;
	my ($header, $body);
	
	($header, $body) = split("\r\n\r\n", $message, 2);
	return $body;
}

sub extract_status_code
{
	my ($message) = shift || return undef;

	if ($message !~ /^(.+)\s+(\d+)/) 
	{
		return undef;
	}
	
	return $2;
}

sub get_302_location
{
	my ($message) = shift || return undef;

	if ($message =~ /.*Location:\s*(.+)\n/i)
	{
		return $1;
	}

	# uhm? where did it go?
	return undef;
}

sub retreive_http_playlist
{
	my ($location) = shift || return undef;
	my ($response);
	my ($status);
	
	while (1) 
	{
		$response = slurp_http($location);
		return undef unless defined $response;
	
		$status = extract_status_code($response);
		if (! defined $status) 
		{
			# problems parsing
			return undef;
		}
	
		if ($status == 200) 
		{
			# 200 OK
			return get_http_body($response);
		}
	
		if ($status == 302) 
		{
			# location moved
			$location = get_302_location($response);
			debug("new location $location\n");
			next;
		}

		# 404, 5XX and anything else
		return undef;
	}
}

sub retreive_playlist
{
	my ($location) = shift || return undef;
	
	if ($location =~ /^(\w+):\/\/(.+)$/) 
	{
		my $protocol = $1;
		my $url = $2;
		
		if ($protocol eq "file") 
		{
			# local file requested
			return slurp_file($url);
		}
		
		if ($protocol eq "http") 
		{
			# remote http file
			return retreive_http_playlist($url);
		}
		
		# unknown protocol
		return undef;
	}
	
	# no protocol specified, assuming local file
	return slurp_file($location);
}

sub slurp_headers
{
	my ($sock) = shift || return undef;
	my ($max_length) = shift || -1;
	my ($data);
	my ($headers) = '';
	
	return "" if ($max_length == 0);
	
	$data = recv_chunk($sock, 1);
	while (defined $data) 
	{
		$headers .= $data;
		last if $headers =~ /\r\n\r\n/;
		
		if ($max_length != -1 && length($headers) >= $max_length) 
		{
			# just enough (we're reading one byte at a time)
			last;
		}
			
		$data = recv_chunk($sock, 1);
	}
	
	return $headers;
}

sub trim
{
	my ($str) = shift || return undef;
	
	$str =~ s/^[\s\t]//g;
	$str =~ s/[\s\t]$//g;
	return $str;
}

sub parse_stream_headers
{
	my ($headers) = shift || return undef;
	my (@lines) = split('\n', $headers);
	my ($server) = {};
	
	foreach my $line (@lines) 
	{
		my ($key, $value);
		
		if ($line =~ /^\s*([\w\-]+)\s*\:\s*(.+)\s*$/) 
		{
			$key = $1;
			$value = $2;
			
			$key = trim($key);
			$value = trim($value);
			
			$server->{$key} = $value;
		}
		
	}
	
	return $server;
}

sub parse_meta
{
	my ($meta) = shift || return undef;
	
	if ($meta =~ /StreamTitle='(.+){1}'/) 
	{
		my $title = $1;
		$title =~ s/\';(.*)$//;
		return $title;
	}
	
	return undef;
}

sub sync_mp3_frame
{
	my ($data) = shift || return undef;
	my ($expected_sync_count) = shift;

	if (! defined $expected_sync_count)
	{
		$expected_sync_count = $max_sync_count;
	}

	# break recursion
	debug("entered recursion with expected = $expected_sync_count, len=" . length($data));
	return $data if ($expected_sync_count == 0);

	my $offset = 0;
	my $max_offset = length($data) - 3;
	while ($offset < $max_offset)
	{
		# look for sync data
		my $frame = unpack('N', substr($data, $offset, $offset + 4));

		if (($frame & 0xfff00000) == 0xfff00000)
		{
			# padding bit
			my $padding = ($frame >> 9) & 1;

			# 0: mpeg1, 1:mpeg2, 2:mpeg2.5
			my $mpg_ver = 0;                 # ISO/IEC 11172-3
			my $ver_idx = ($frame >> 19) & 3;
			$mpg_ver = 1 if ($ver_idx == 2); # ISO/IEC 13818-3
			$mpg_ver = 2 if ($ver_idx == 0); # unofficial
			goto next_sync if $ver_idx == 1; # reserved

			# find mpeg layer (0 for Layer I)
			my $layer = 3 - (($frame >> 17) & 3);
			goto next_sync if $layer == 3; # reserved

			my $sample_rate = $freq_table[($frame >> 10) & 3][$mpg_ver];

			my $br_idx = 0;
			if ($mpg_ver == 0)
			{
				# easy. MPEG1
				$br_idx = $layer;
			}
			else
			{
				# MPEG2 and MPEG2.5
				$br_idx = 3 if ($layer == 0);
				$br_idx = 4 if ($layer > 0);
			}

			my $bitrate = 1000 * $bitrate_table[($frame >> 12) & 0xf][$br_idx];

			my $frame_size = int(144 * $bitrate / ($sample_rate)) + $padding;
			debug("frame_size $frame_size");

			# recursively find more sync bits
			if (($offset + $frame_size) > $max_offset)
			{
				# impossible for another frame to be found
				return undef;
			}

			my $subdata = substr($data, $offset + $frame_size);
			my $rec = sync_mp3_frame($subdata, $expected_sync_count - 1);
			if (defined $rec)
			{
				# recursion ended!
				return $subdata;
			}
		}

		next_sync:
		
		if ($expected_sync_count < $max_sync_count)
		{
			# we are not allowed to continue loop inside recursion
			last;
		}

		$offset++;
	}

	return undef;
}

sub recv_metablock
{
	my ($sock) = shift || return undef;
	my ($block_size);
	my ($data);
	
	$block_size = recv_chunk($sock, 1);
	$block_size = ord($block_size) * 16;
	return "" if ($block_size == 0);
	
	$data = recv_chunk($sock, $block_size);
	return $data;
}

sub fix_filename
{
	my ($fn) = shift || return undef;

	# remove all characters that cause problems
	# on unices and on windows
	$fn =~ s/[\\\/\?\*\:\t\n\r]//g;
	return $fn;
}

sub open_output
{
	my ($context) = shift || return 0;
	my ($fn) = shift || return 0;

	$fn = fix_filename($fn);
	open(OUTPUT, ">$fn") || die "FIXME: ";
	OUTPUT->autoflush(1);
	binmode OUTPUT;
	$context->{output_open} = 1;
	return 1;
}

sub write_block
{
	my ($chunk) = shift || return;
	my ($context) = shift || return;

	if ($config->{stdout} == 1) 
	{
		print $chunk;
	}

	# allow set name support
	if (defined($config->{name})) 
	{
		$context->{title} = $config->{name};
		$context->{id} = 0; # it doesn't mean anything in this context anyway
	}
	
	if ($context->{output_open} == 0 && $context->{title} ne '') 
	{
		my $trackid = '';
		if ($context->{id} != 0) 
		{
			$trackid = sprintf "%02d - ", $context->{id};
		}

		my $fn = $trackid . $context->{title};
		$fn .= defined $context->{'is-ogg'} ? ".ogg" : ".mp3";
		return unless open_output($context, $fn);
	}

	if ($context->{output_open} == 1) 
	{
		print OUTPUT $chunk;
	}
}

sub print_title
{
	my ($context) = shift;
	
	if ($config->{quiet} == 1) 
	{
		# quiet!
		return;
	}

	if (defined $context) 
	{
		if ($context->{length} > 0) 
		{
			my $trackid = '';
			if ($context->{id} != 0) 
			{
				$trackid = sprintf "%02d - ", $context->{id};
			}

			my ($kb) = int(($context->{length} + 1023) / 1024);
			print "\r${trackid}$context->{title} [$kb K]";
		}
	}
	else 
	{
		print "\n";
	}
}

sub close_output_stream
{
	my $context = shift || return;

	# close old output stream
	$context->{output_open} = 0;
	close OUTPUT;
}

sub set_title
{
	my ($context) = shift || return 0;
	my ($newtitle) = shift || return 0;
	
	if ($newtitle eq $context->{title}) 
	{
		# still playing the same track
		return 0;
	}

	if ($context->{title} ne '') 
	{
		# new track
		print_title();
		$config->{'played-tracks'}++;
	}

	$context->{title} = $newtitle;	
	
	# track has changed
	if ($config->{tracks} == 0) 
	{
		# there is no need to switch output stream
		return 1;
	}

	# reset track information
	$context->{length} = 0;
	$context->{id} = $context->{id} + 1;

	close_output_stream($context);
	return 1;
}

sub loop_named_stream
{
	my ($sock) = shift || return 0;
	my ($stream) = shift || return 0;
	my ($context) = {};

	debug("loop_named_stream()");

	my $synced = 0;
	my $huge = "";

	$context->{id} = find_latest_index(".");
	$context->{title} = '';
	$context->{length} = 0;
	$context->{output_open} = 0;
	$context->{'is-ogg'} = $stream->{'is-ogg'};

	if ($config->{tracks} == 0) 
	{
		# single audio track of whatever is received
		$context->{title} = $stream->{'name'};
	}

	# load all data up to the first metaint if -t is set
	elsif ($config->{traks})
	{
		my $metablock;
		my $title;

		while ($config->{stop} == 0) 
		{
			my $chunk = recv_chunk($sock, $stream->{'metaint'});
			if (length($chunk) < $stream->{'metaint'}) 
			{
				print "got a problem here..\n";
				return 0;
			}

			$huge .= $chunk;
			$metablock = recv_metablock($sock);
			$title = parse_meta($metablock);
			last if defined $title;

			if (length($huge) > $largest_unknown_buffer)
			{
				debug("too many bytes before title received");

				if ($config->{quiet} == 0)
				{
					print "no title was received. giving up";
				}

				return 0;
			}
		}

		set_title($context, $title);
		$context->{length} += length($huge);		

		if ($config->{sync} != 0)
		{
			$huge = sync_mp3_frame($huge);
			if (defined $huge)
			{
				write_block($huge, $context);
				$synced = 1;
			}
		}
		else
		{
			write_block($huge, $context);
		}

		print_title($context);
	}

	$huge = "";	
	while (1) 
	{
		check_stop_cond();
		last if ((defined $config->{stop}) && ($config->{stop} != 0));
			
		my $chunk = recv_chunk($sock, $stream->{'metaint'});
		if (length($chunk) < $stream->{'metaint'}) 
		{
			print "got a problem here..\n";
			return 0;
		}

		# update statistics
		$config->{'bytes-downloaded'} += length($chunk);
		$context->{length} += length($chunk);
		
		if ($synced)
		{
			write_block($chunk, $context);
		}
		else
		{
			$huge .= $chunk;
			my $sync_frame = sync_mp3_frame($huge);
			if (defined $sync_frame)
			{
				write_block($sync_frame, $context);
				$huge = "";
				$synced = 1;
			}	
		}	

		print_title($context);
		
		my $metablock = recv_metablock($sock);
		
		# update current track if title found
		my $title = parse_meta($metablock);
		set_title($context, $title) if defined $title;
	}
	
	debug("loop_named_stream ended");
	return 1;
}

sub loop_anonymous_stream
{
	my ($sock) = shift || return 0;
	my ($stream) = shift || return 0;
	my ($context) = {};

	debug("loop_anonymous_stream()");

	$context->{id} = 0;
	$context->{title} = defined $stream->{name} ? $stream->{name} : 'stream-' .time;
	$context->{length} = 0;
	$context->{output_open} = 0;
	$context->{'is-ogg'} = $stream->{'is-ogg'};

	while (1) 
	{
		check_stop_cond();
		last if ((defined $config->{stop}) && ($config->{stop} != 0));

		my $chunk = recv_chunk($sock, 1024);
		last unless length($chunk) > 0;

		# update statistics
		$config->{'bytes-downloaded'} += length($chunk);

		$context->{length} += length($chunk);
		write_block($chunk, $context);
		print_title($context);
	}
	
	debug("loop_anonymous_stream ended");
	return 1;
}

sub strip_protocol
{
	my ($url) = shift || return undef;

	if ($url =~ /^\w+:\/\/(.+)$/) 
	{
		return $1;
	}

	return $url;
}
		
sub split_protocol
{
	my ($url) = shift || return undef;

	if ($url =~ /^(\w+):\/\//) 
	{
		return $1;
	}

	return undef;
}

sub prepare_stream_data
{
	my ($raw) = shift || return undef;
	my ($out) = ();

	# ICY protocol
	if (defined $raw->{'icy-name'}) 
	{
		$out->{name} = $raw->{'icy-name'};
	}

	if (defined $raw->{'icy-metaint'}) 
	{
		$out->{metaint} = $raw->{'icy-metaint'};
	}

	if (defined $raw->{'icy-genre'}) 
	{
		$out->{genre} = $raw->{'icy-genre'};
	}

	# Shoutcast protocol
	if (defined $raw->{'x-audiocast-genre'}) 
	{
		$out->{genre} = $raw->{'x-audiocast-genre'};
	}

	if (defined $raw->{'x-audiocast-name'}) 
	{
		$out->{name} = $raw->{'x-audiocast-name'};
	}

	return $out;
}

sub start_stream
{
	my ($location) = shift || return 0;
	my ($host, $port, $path);
	my ($sock, $headers);
	my ($status);
	my ($stream_data);

	do
	{
		if (split_protocol($location) ne "http") 
		{
			print STDERR "error: not an http location $location\n";
			return 0;
		}

		$location = strip_protocol($location);

		# XXX: note: can clean this (too much code)
	
		# parse location
		($host, $port, $path) = split_url($location);
	
		# parsing errors?
		if (! defined $host) 
		{
			print STDERR "error parsing url $location\n";
			return 0;
		}

		$port = 80 unless defined $port;
		$path = "/" unless defined $path;
	
		$sock = IO::Socket::INET->new(PeerAddr => $host, PeerPort => $port, Proto => 'tcp');
		if (! defined $sock) 
		{
			print STDERR "error connecting to $host:$port\n";
			return 0;
		}

		my $agent = $config->{'user-agent'};
		my $request = "GET $path HTTP/1.0\r\n" .
			"Host: $host:$port\r\n" .
			"Accept: ${accept_header}\r\n" .
			"Icy-MetaData:1\r\n" .
			"User-Agent:$agent\r\n" .
			"\r\n";

		debug("sending request to server", $request);
		print $sock $request;

		$headers = slurp_headers($sock);
		if (! defined $headers) 
		{
			print STDERR "error retreiving response from server\n";
			return 0;
		}

		debug("data retreived from server", $headers);

		$status = extract_status_code($headers);
		if (! defined $status) 
		{
			print STDERR "error parsing server response (use --debug)\n";
			return 0;
		}

		elsif ($status == 302) 
		{
			# relocated
			$location = get_302_location($headers);
		}

		elsif ($status == 400) 
		{
			# server full
			print STDERR "error: server is full (use --debug for complete response)\n";
			return 0;
		}

		elsif ($status != 200) 
		{
			# nothing works fine these days
			print STDERR "error: server error $status (use --debug for complete response)\n";
			return 0;
		}

	} while ($status != 200);

	# manage icy and x-audiocast headers even if they are embedded in http
	# but skip header manipulation in other cases!
	if (($headers =~ /.*icy.*/) or ($headers =~ /.*audiocast.*/))
	{
		my $raw_stream_data = parse_stream_headers($headers);
		if (! defined $raw_stream_data) 
		{
			print STDERR "error: problems parsing stream headers (please use --debug)\n";
			return 0;
		}

		$stream_data = prepare_stream_data($raw_stream_data);
		if (! defined $stream_data->{'name'}) 
		{
			print STDERR "error: not an icecast/shoutcast stream\n";
			return 0;
		}

		if ($config->{debug}) 
		{
			my $info = "name: $stream_data->{name}\n";
			$info .= "genre: $stream_data->{genre}\n" if defined $stream_data->{genre};
			$info .= "metaint: $stream_data->{metaint}\n" if defined $stream_data->{metaint};
			debug("parsed stream headers", $info);
		}

		if ($headers =~ /.*Content-Type: application\/ogg/i)
		{
			# streaming url is .ogg file,
			# remember this when saving output file
			$stream_data->{'is-ogg'} = 1;
		}
	}

	if (defined $stream_data->{'metaint'}) 
	{
		# server periodically sends stream title
		loop_named_stream($sock, $stream_data);
	} 
	else {
		# no titles for tracks
		loop_anonymous_stream($sock, $stream_data);
	}
	
	return 1;
}

sub banner()
{
	print "$version\n";
}

sub help()
{
	banner();
	
	print "usage: icecream [options] URL [URL...]\n";
	print "\n";
	print "options:\n";
	print "  -h, --help          print this message\n";
	print "  -q, --quiet         no printouts\n";
	print "  -v, --verbose       be verbose\n";
	print "  -t, --tracks        split into tracks when saving\n";
	print "  --name=NAME         save stream to file NAME. Format codes\n";
	print "                      are replaced as in the date command.\n";
	print "  --stop=N[units]     stop download after N (kb, mb, min, songs)\n";
	print "  --user-agent=AGENT  identify as AGENT stead of ${def_agent}\n";
	print "  --stdout            output stream to stdout (implies quiet)\n";
	print "  --sync              sync mpeg audio\n";
	print "  --debug             turn on debugging\n";
	exit 0;
}

sub parse_options
{
	my (%options) = ();
	my ($config) = {};
	
	GetOptions(\%options, "--help", "--quiet", "--verbose", "--stdout", "--tracks", "--debug", "--user-agent=s", "--name=s", "--stop=s", "--sync");

	$config->{help} = (defined $options{help}) ? 1 : 0;
	$config->{quiet} = (defined $options{quiet}) ? 1 : 0;
	$config->{verbose} = (defined $options{verbose}) ? 1 : 0;
	$config->{debug} = (defined $options{debug}) ? 1 : 0;
	$config->{stdout} = (defined $options{stdout}) ? 1 : 0;
	$config->{tracks} = (defined $options{tracks}) ? 1 : 0;
	$config->{sync} = (defined $options{sync}) ? 1 : 0;
	$config->{name} = (defined $options{name}) ? $options{name} : undef;
	$config->{'user-agent'} = (defined $options{'user-agent'}) ? $options{'user-agent'} : ${def_agent}; 
	$config->{'stop-cond'} = (defined $options{stop}) ? lc $options{stop} : undef;

	# stdout implies quiet
	if ($config->{stdout} == 1) 
	{
		# stdout implies quiet
		$config->{quiet} = 1;
		$config->{debug} = 0;
	}

	# Do Date replacement on name field
	if (($config->{name}) && ($config->{name} =~ /%/)) 
	{
		require POSIX;
		POSIX->import();
		$config->{name} = strftime($config->{name},localtime(time));
	}
	
	# validate stop condition
	if (defined $config->{'stop-cond'}) 
	{
		my $cond_valid = 0;
		if ($config->{'stop-cond'} =~ /^(\d+)(\w+)$/) 
		{
			my $cond = $2;
			if ($cond eq 'min' || $cond eq 'songs' || $cond eq 'kb' || $cond eq 'mb') 
			{
				$cond_valid = 1;
			}
		}

		if ($cond_valid == 0)
		{
			print STDERR "error parsing stop condition $config->{'stop-cond'}\n";
			return undef;
		}
	}

	$config->{urls} = join("\n", @ARGV);
	return $config;
}

sub verbose
{
	my $s = shift || return;

	if ($config->{verbose} == 1) 
	{
		print STDERR "$s";
	}
}

sub debug
{
	my $title = shift || return;
	my $additional = shift;

	if ($config->{debug}) 
	{
		print "[ $title ]\n";
		if (defined $additional) 
		{
			my @ar = split("\n", $additional);
			foreach my $s (@ar) 
			{
				print "\t$s\n";
			}
		}
	}
}

sub process
{
	my ($url) = shift || return undef;
	my ($config) = shift || return undef;
	
	# play direct stream url (not .pls nor .m3u)
	if (($url =~ /^http/) and (not (($url =~ /\.m3u$/) or ($url =~ /\.pls$/))))
	{
		start_stream($url);
		return 1;
	}

	my $raw = retreive_playlist($url);
	if (! defined $raw) 
	{
		print STDERR "error: failed to retreive playlist from $url\n";
		return undef;
	}

	my @pls = ();

	if ($url =~ /\.m3u$/) 
	{
		@pls = parse_m3u_playlist($raw);
	} 
	elsif ($url =~ /\.pls$/)
	{
		@pls = parse_pls_playlist($raw);
	}

	debug("play list parsed");

	$config->{'stop'} = 0;
	$config->{'played-tracks'} = 0;
	$config->{'bytes-downloaded'} = 0;
	$config->{'start-time'} = time();

	my $entry = ();
	foreach $entry (@pls) 
	{
		next unless defined $entry;

		if ($config->{verbose}) 
		{
			print "[ playing $entry->{'file'} ]\n";
		}

		start_stream($entry->{file});
		last if ($config->{stop} != 0);
	}
	
	return 1;
}

sub main { 
	
	my (@queue, $url);
	my ($played) = 0;
	
	$config = parse_options();
	if (! defined $config) 
	{
		# there was an error parsing parameters
		help();
	}

	help() if ($config->{help} == 1);
	
	@queue = split("\n", $config->{urls});
	help() unless @queue > 0;
	
	foreach $url (@queue) 
	{
		process($url, $config);
		$played++;
	}

	print "\n";

	if ($played == 0) 
	{
		print STDERR "nothing was played";
	}
}		

sub find_latest_index
{
	my ($location) = shift || return 0;
	my ($id) = 0;
	my ($fn);

	opendir(DIR, $location) || return $id;
	while ($fn = readdir(DIR)) 
	{
		if ($fn =~ /^(\d+)\s+.*\.mp3$/) 
		{
			$id = $1 if ($id < $1);
		}
	}
				
	closedir(DIR);
	return $id;
}

# great C habit
binmode STDOUT;
$| = 1;

main();

__END__

=head1 NAME

icecream - download icecast and shoutcast streams, redirecting all fetched
content to stdout and/or to disk at the same time

=head1 SYNOPSIS

icecream [OPTIONS] URL [URL..]

=head1 DESCRIPTION

icecream is a lightweight, non-interactive, stream download utility.
It connects to icecast and shoutcast servers or direct stream URLs, and
redirects all fetched content to stdout and/or to media files on your disk. 

Listen to the stream piping the output to a stdin-capable media player.
Save the stream to a named file or split it into different tracks.
It is possible to redirect the stream and save it to disk at the same time.

icecream is able to parse pls and m3u playlists, and to download mp3 and ogg
direct stream URLs. If the stream is anonymous it will be saved as
'stream-time.mp3', where time is actual timestamp.

=head1 OPTIONS

=over 8

=item B<-h>, B<--help>

Print a help message describing all options

=item B<-q>, B<--quiet>

Turn off output

=item B<-v>, B<--verbose>

Be verbose

=item B<-t>, B<--tracks>

Split stream into tracks (if possible)

=item B<--name=NAME>

Save the stream to file specified by NAME. Format codes starting with "%" will
be replaced. See the date command for valid format codes.

=item B<--stop=N[units]>

Stop downloading the stream after N kb/mb/min/songs

=item B<--user-agent=AGENT>

Set user-agent header to AGENT

=item B<--stdout>

Output stream to stdout (implies -q)

=item B<--sync>

Turn syncing on, required for some mpeg players that read from stdin

=item B<--debug>

Turn on debugging outputs


=back

=head1 EXAMPLES

=over 8

=item Streaming to mpg123

icecream --stdout http://radio.com/playlist.pls | mpg123 -

=item Split stream into different tracks

icecream -t http://metal.org/radio.pls

=item Split stream into tracks and play with vlc at the same time

icecream -t --stdout http://streaming.com/playlist.pls | vlc file:/dev/stdin

=item Prepare a 74 minute CD

icecream -t --stop 74min http://trace.net/playlist.m3u 

=item Use a filename with today's date as output

icecream -q --name 'radio_%Y_%m_%d' --stop 60min http://radio.com/playlist.pls

=back

=head1 BUGS

You are welcome to send bug reports about icecream to our mailing list.
Feel free to visit http://icecream.sourceforge.net

=head1 AUTHOR

Written by Gil Megidish <gil at megidish.net>

=cut

