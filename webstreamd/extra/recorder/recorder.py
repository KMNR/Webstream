import urllib2
import argparse
import logging
import re
import struct
from datetime import datetime

DEFAULT_AGENT = 'pycream/0.1'
VERSION = 'pycream/0.1'

DEFAULT_TIMEOUT = 500
MAX_SYNC_COUNT = 3
LARGEST_UNKNOWN_BUFFER = 1024**2

BITRATE_TABLE = 
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
    )

FREQ_TABLE =
    (
        [44100, 22050, 11025],
        [48000, 24000, 12000],
        [32000, 16000, 8000],
        [1, 1, 1, 1]
    )

def main():
    parser = argparse.ArgumentParser(description='Records a webstream for a specified duration')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet', type=bool, default=False,
        help="turn off output")
    group.add_argument('-v', '--verbose', type=bool, default=False,
        help="be verbose")
    group.add_argument('--debug', type=bool, default=False,
        help="turn on debugging outputs")
    group.add_argument('--stdout', type=bool, default=False,
        help="output stream to stdout (implies -q)")
    parser.add_argument('-t', '--tracks', type=bool, default=False,
        help="split stream into tracks (if possible)")
    parser.add_argument('--name', dest='name',
        help="save the stream to file specified by name. format codes starting with ``%'' will be replaced. see the date command for valid format codes.")
    parser.add_argument('--stop', dest='stop',
        help="stop downloading the stream after n kb/mb/min/songs")
    parser.add_argument('--user-agent', dest='agent',
        help="set user-agent header to agent")
    parser.add_argument('--sync', type=bool, default=False,
        help="turn syncing on, required for some mpeg players that read from stdin")

    args = parser.parse_args()
    if args.debug:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.CRITICAL
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format='%(levelname)s:%(message)s', level=level)
    print args
    
def parse_stop_condition(stopcond):
    m = re.search('^(\d+)(\w+)$', stopcond)
    amnt = m.group(1)
    unit = m.group(2)
    return (amnt,unit)
    
def parse_m3u_playlist(fp):
    streams = []
    id = 1
    for line in fp:
        if re.search('^#EXT'):
            continue
        streams.append({'id':id, 'file':line.strip()})
    return streams
    
def parse_pls_playlist(fp):
    streams = []
    first = fp.readline()
    if re.search('^\[playlist\]', flags=re.IGNORECASE):
        raise ValueError('Incorrectly formatted pls file')
    
    for line in fp:
        if not line:
            continue
        m = re.search('^(\w+)(\d+)=(.+)$')
        if m:
            property = m.groups(1)
            id = m.groups(2)
            value = m.groups(3).strip()
            streams.append({'property': property.lower(), 'value': value})
    return streams
    
def recv_chunk(fp, count):
    data = []
    while count > 0:
        next_chunk = count if count > 0 else 1024
        
        chunk = fp.read(next_chunk)
        if len(data) == 0:
            break
            
        data += chunk
        count -= len(data)
    return data

def parse_meta(self,meta):
    m = re.search('(.+){1}')
    if not m:
        raise ValueError("No meta pattern match in {}".format(meta))
       
    meta = m.groups(1)
    return = re.sub('\';(.*)$','',meta)
    
def sync_mp3_frame(self, data, expected_sync_count=None):
    if expected_sync_count == None:
        expected_sync_count = MAX_SYNC_COUNT
     
    logging.debug("entered recursion with expected = {}, len={}".format(expected_sync_count,length($data)))
    if expected_sync_count == 0:
        return data
    
    offset = 0
    max_offset = len(data) - 3
    
    for i in xrange(offset,max_offset):
        frame = struct.unpack('>L', data[offset:offset+4])
        do_next_sync = False
        if (frame & 0xfff00000) == 0xfff00000:
            padding = (frame >> 9) & 1
            mpg_ver = 0 # 0 mpeg1, 1 mpeg2, 2 mpeg2.5
            ver_idx = (frame >> 19) & 3
            if ver_idx == 2:
                mpg_ver = 1
            elif ver_idx == 0:
                mpg_ver = 2
            layer = 3 - ((frame >> 17) & 3)
            if layer != 3 and mpg_ver != 0:
                sample_rate = FREQ_TABLE[(frame >> 10) & 3][mpg_ver]
                br_idx = 0
                if mpg_ver == 0:
                    br_idx = layer
                elif layer == 0:
                    br_idx = 3
                elif layer > 0:
                    br_idx = 4
                
                bitrate = 1000 * BITRATE_TABLE[(frame >> 12) & 0xf][br_idx]
                framesize = int(144 * bitrate / sample_rate) + padding
                logging.debug("frame_size {}".format(framesize))
            
                # recursively find more sync bits
                if offset + frame_size > max_offset:
                    # impossible for another frame to be found
                    return None

                subdata = data[(offset+frame_size):]
                rec = sync_mp3_frame(subdata, expected_sync_count-1)
                if rec != None:
                    return subdata
        
        if expected_sync_count < max_sync_count:
            break
    return None
    
def recv_metablock(fp):
    block_size = self.recv_chunk(fp,1)
    block_size = ord(block_size) * 16
    return "" if blocksize == 0 else recv_chunk(fp, block_size)

def fix_filename(fn):
    return re.sub('[\\\/\?\*\:\t\n\r]','',fn)

def open_ouput(fn):
    fn = self.fix_filename(fn)
    fp = open(fn, 'w+', 0)
    self.output = fp    
  
class Recorder(object):
    def __init__(self, stream, name, output, stop=None, tracks=False, agent=None, sync=False):
        self.name = name
        self.stop = parse_stop_condition(stop) if stop else None
        self.tracks = tracks
        self.agent = agent if agent else DEFAULT_AGENT
        self.sync = sync
        self.bytes_read = 0
        self.start_time = datetime.today()
        self.stopping = False
        self.tracks = 0
        self.stream = stream
        self.output = output
    
    def check_stop_condition(self):
        if self.stop == None:
            return False
            
        kb = self.bytes_read / 1024
        amnt,unit = self.stop
        
        b = False
        if unit == 'kb':
            b = (kb > amnt)
        elif unit == 'mb':
            b = (kb > amnt*1024)
        elif unit == 'min':
            elapsed = datetime.today() - self.start_time
            elapsed = elapsed.total_seconds() / 60
            b = (elapsed > amnt)
        elif unit == 'songs':
            b = (self.tracks > amnt)
        else:
            raise ValueError("Invalid Unit: {}".format(unit))
        
        self.stopping = b
        return b
   
    def retreive_playlist(self,url):
        headers = { 'User-Agent' : self.agent }
        req = urllib2.Request('url', None, headers)
        return urllib2.urlopen(req).read()


    def write_block(self, chunk):
        if self.name:
            self.title = self.name
            
     
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


def stream():
    f = urllib2.urlopen('http://www.python.org/')
    print f.read(100)



if __name__ == "__main__":
    main() 
