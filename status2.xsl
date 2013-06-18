<xsl:stylesheet xmlns:xsl = "http://www.w3.org/1999/XSL/Transform" version = "1.0" >
<xsl:output omit-xml-declaration="yes" method="html" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" encoding="UTF-8" />
<xsl:template match = "/icestats" >
{
"MountPoints": [
<xsl:for-each select="source">
  {
    "MountPoint":"<xsl:value-of select="@mount" />",
    "Name":"<xsl:value-of select="server_name" />",
    "CurrentListeners":<xsl:value-of select="listeners" />,
    "PeakListeners":<xsl:value-of select="listener_peak" />,
    "Description":"<xsl:value-of select="server_description" />",
    "Genre":"<xsl:value-of select="genre" />",
    "CurrentlyPlaying":"<xsl:value-of select="artist" /> - <xsl:value-of select="title" />",
    "URL":"<xsl:value-of select="server_url" />"
  },
</xsl:for-each>
  {
    "MountPoint":"Global",
    "ClientConnections":<xsl:value-of select="connections" />,
    "CurrentListeners":<xsl:value-of select="listeners" />
  }
]
}
</xsl:template>
</xsl:stylesheet>
