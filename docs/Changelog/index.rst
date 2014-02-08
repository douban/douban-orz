Changelog
^^^^^^^^^

ORZ 0.4@2014-02-08
''''''''''''''''''''

[Feature]:

    0. 增加清除缓存的接口

[Refactor]:

    1. 去除ORZ.__init__ 对于 ORZ.exports的依赖, 以便于导入__version__

ORZ 0.3.3@2014-02-07
''''''''''''''''''''

[BugFix]:

    0. 修正文档中例子代码

[Refactor]:

    0. 清理v0.1时候的遗留代码，合并OrmItem 到 OrzField


ORZ 0.3.0@2014-01-15
''''''''''''''''''''

0. 使用OrzBase 以及 Nested Class OrzMeta 来代替orz\_decorate;
   orz\_decorate只是废弃了，但在这个版本中仍然可以照常使用。具体区别可以见PR2637
1. 增加了事务
2. 优化了性能
3. 优化了默认值的处理(具体见文档)
4. 整了一个文档的雏形


