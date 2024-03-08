from typing import Any, Optional
import scrapy
from urllib.parse import urlparse
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from educrawlerServicev1.utils import removeEmptySpaceParagraph, removeHTMLTag, removeEmptyLine, countLetterInParagraph, countExistedTimesTokenize
import math
from scrapy import signals

class DemoCrawlerURL(scrapy.Spider):
  name = "demoCrawlerURL"
  allowed_domains = []
  start_urls = []
  allowed_file_format = []
  allowed_keyword = [
    "giáo dục",
    "đại học",
    "trường",
    "học",
    "dạy",
    "phổ thông",
    "tiểu học",
    "mầm non",
    "giáo viên",
    "đào tạo",
    "nghề",
    "sinh viên",
    "học sinh",
    "ngành",
    "khoa",
    "trung học",
    "môn",
    "ngữ văn",
    "bài tập",
    "chuyên",
    "học đường",
    "trải nghiệm",
    "vận động",
    "kĩ năng",
    "kiến trúc",
    "học tập",
    "kĩ năng mềm",
    "rèn luyện",
    "giảng viên",
    "sư phạm",
    "tư duy",
    "phân tích",
    "thực nghiệm",
    "giải quyết vấn đề",
    "toán",
    "tự học",
    "hướng dẫn",
    "đánh giá",
    "kết quả",
  ]

  uncrawlable_link = [
    "mailto", "javascript", "commentbox", "tel"
  ] 
  
  def __init__(self, link: str, name: Optional[str] = None, **kwargs: Any):   
    super(DemoCrawlerURL, self).__init__(name, **kwargs)
    
    self.start_urls.append(link)
        
    for url in self.start_urls:
      parsed_uri = urlparse(url)
      domain = '{uri.netloc}'.format(uri=parsed_uri)
      self.allowed_domains.append(domain)
      
    self.spider_type = "demo"
    
  @classmethod
  def from_crawler(cls, crawler, *args, **kwargs):
    spider = super(DemoCrawlerURL, cls).from_crawler(crawler, *args, **kwargs)
    crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
    return spider
  
  def start_requests(self):
    for url in self.start_urls:
      yield scrapy.Request(
        url=url, 
        callback=self.parse,
        errback=self.errback_httpbin,
      )
      
  def spider_closed(self, spider):
    pass
  
  def parse(self, response):
    converted_headers = self.convert(response.headers)
    
    if ("text/html" in converted_headers["Content-Type"]):
      academic_keywords = 0
    
      # Crawl Basic Data
      websiteTitle = response.css('title::text').get()
      content   = response.css('p').getall()
          
      # Content Checking and Reformatted
      found_keywords = []
      raw_content = " ".join(content)
      raw_content = removeHTMLTag(raw_content)
      raw_content = removeEmptyLine(raw_content)
      raw_content = removeEmptySpaceParagraph(raw_content)
      total_words = countLetterInParagraph(raw_content)
      minimum_keywords = math.floor(total_words * 1.0 / 200)

      # Check academic content      
      for keyword in self.allowed_keyword:
        count = countExistedTimesTokenize(websiteTitle, keyword)
        if count > 0:
          found_keywords.append(keyword)
          academic_keywords += count
      
        count = countExistedTimesTokenize(raw_content, keyword)
        if count > minimum_keywords:
          found_keywords.append(keyword)
          academic_keywords += count
          
      # Check before save
      if len(self.allowed_keyword) == 0 or (len(self.allowed_keyword) > 0 and academic_keywords > 0):
        items = {
          "crawlerType": "demo",
          "domain": self.allowed_domains[0],
          "url": response.url,
          "academic_keyword": academic_keywords,
          "keywords": found_keywords,
          "title": websiteTitle,
          "reformatted_content": raw_content,
          "total_words": total_words,
          "minimum_keywords": minimum_keywords
        }
        yield items
        
  def errback_httpbin(self, failure):
    # log all failures
    self.logger.error(repr(failure))

    if failure.check(HttpError):
      # these exceptions come from HttpError spider middleware
      # you can get the non-200 response
      response = failure.value.response
      self.logger.error("HttpError on %s", response.url)

    elif failure.check(DNSLookupError):
      # this is the original request
      request = failure.request
      self.logger.error("DNSLookupError on %s", request.url)

    elif failure.check(TimeoutError, TCPTimedOutError):
      request = failure.request
      self.logger.error("TimeoutError on %s", request.url)
    
  def convert(self, data):
    if isinstance(data, bytes):  return data.decode('ascii')
    if isinstance(data, list):   return data.pop().decode('ascii')
    if isinstance(data, dict):   return dict(map(self.convert, data.items()))
    if isinstance(data, tuple):  return map(self.convert, data)
    return data