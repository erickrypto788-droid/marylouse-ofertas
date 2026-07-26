<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <html>
      <head>
        <title>MaryLouse Ofertas — Feed RSS</title>
        <meta charset="UTF-8"/>
        <style>
          body { margin: 0; font-family: Arial, Helvetica, sans-serif; background: linear-gradient(180deg, #fff4f8, #ffffff); color: #1f1720; }
          .wrap { max-width: 980px; margin: 40px auto; padding: 0 20px; }
          .hero { background: #fff; border: 1px solid #f0d7df; border-radius: 28px; padding: 28px; box-shadow: 0 16px 35px rgba(154, 41, 92, .10); }
          h1 { margin: 0 0 8px; color: #064750; font-size: 36px; }
          p { color: #6e5e67; font-size: 17px; }
          .item { display: block; background: #fff; border: 1px solid #f0d7df; border-radius: 20px; padding: 18px; margin-top: 14px; text-decoration: none; color: inherit; }
          .item strong { color: #ef2473; font-size: 19px; }
          .btn { display: inline-block; margin-top: 18px; padding: 13px 18px; border-radius: 999px; background: #ef2473; color: #fff; text-decoration: none; font-weight: 900; }
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="hero">
            <h1>MaryLouse Ofertas — Feed RSS</h1>
            <p>Últimas ofertas publicadas automaticamente. Você também pode usar este link em leitores RSS.</p>
            <a class="btn" href="/">Voltar para o site</a>
          </div>
          <xsl:for-each select="rss/channel/item">
            <a class="item">
              <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
              <strong><xsl:value-of select="title"/></strong>
              <p><xsl:value-of select="description"/></p>
            </a>
          </xsl:for-each>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
