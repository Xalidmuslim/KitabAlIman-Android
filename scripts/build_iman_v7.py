"""v0.7 Quran citation punctuation fix; no source text changes."""
from pathlib import Path
import argparse,re
from scripts.build_iman_v6 import build_v6

def verse_slices(text):
    ref=re.compile(r'»\s*[\[(]\s*\d{1,3}:\d{1,3}(?:[–-]\d{1,3})?\s*[\])]')
    slices=[];cursor=0
    for m in ref.finditer(text):
        depth=0;start=-1
        for pos in range(m.start(),-1,-1):
            if text[pos]=='»':depth+=1
            elif text[pos]=='«':
                depth-=1
                if depth==0:start=pos;break
        if start<cursor or start<0:continue
        end=m.end()
        while end<len(text) and text[end] in '.,;:!?':end+=1
        while end<len(text) and text[end].isspace():end+=1
        if start>cursor:slices.append((cursor,start,False))
        slices.append((start,end,True));cursor=end
    if cursor<len(text):slices.append((cursor,len(text),False))
    return slices

def patch_reader(source):
    old='''        if (start < cursor || start < 0) continue
        if (start > cursor) result.add(QuranSlice(cursor, start, false))
        result.add(QuranSlice(start, match.range.last + 1, true))
        cursor = match.range.last + 1'''
    new='''        if (start < cursor || start < 0) continue
        // Keep sentence punctuation with the Quran quote, never as the first
        // character of an adjacent prose paragraph.
        var end = match.range.last + 1
        while (end < text.length && text[end] in ".,;:!?") end++
        while (end < text.length && text[end].isWhitespace()) end++
        if (start > cursor) result.add(QuranSlice(cursor, start, false))
        result.add(QuranSlice(start, end, true))
        cursor = end'''
    if source.count(old)!=1:raise RuntimeError('Pinned QuranSlice parser changed')
    return source.replace(old,new,1)

KOTLIN_TEST=r'''package com.xalid.meditsinaproroka.nativeapp
import org.junit.Assert.*
import org.junit.Test
class ImanReaderV7Test {
    @Test fun referencePunctuationDoesNotStartAnotherParagraph() {
        val text="Аллах сказал: «Аят» [40:10]. Это объяснение."
        val slices=citedVerseSlices(text)
        assertEquals(text,slices.joinToString(""){text.substring(it.start,it.endExclusive)})
        assertEquals("«Аят» [40:10]. ",text.substring(slices.first{it.isVerse}.start,slices.first{it.isVerse}.endExclusive))
        assertEquals("Это объяснение.",text.substring(slices.last().start,slices.last().endExclusive))
    }
    @Test fun commaAndSecondCitationAreNotOrphaned() {
        for (text in listOf("Аллах сказал: «Аят» [48:18], слова Всевышнего.",
           "Аллах сказал: «Аят» [7:196]. Затем сказал: «Другой аят» [45:19]. Пояснение.")) {
            val slices=citedVerseSlices(text)
            assertEquals(text,slices.joinToString(""){text.substring(it.start,it.endExclusive)})
            for (index in slices.indices) {
                val s=slices[index]
                if (!s.isVerse && index>0) {
                    assertFalse(text.substring(s.start,s.endExclusive).startsWith("."))
                    assertFalse(text.substring(s.start,s.endExclusive).startsWith(","))
                }
            }
        }
    }
}
'''

def build_v7(kit,destination):
    build_v6(kit,destination)
    gradle=destination/'app/build.gradle'
    text=gradle.read_text(encoding='utf-8')
    for old,new in [('versionCode 6','versionCode 7'),("versionName '0.6.0'","versionName '0.7.0'"),("applicationIdSuffix '.preview6'","applicationIdSuffix '.preview7'")]:
        if text.count(old)!=1:raise RuntimeError('Unexpected Gradle '+old)
        text=text.replace(old,new,1)
    gradle.write_text(text,encoding='utf-8')
    root=destination/'app/src/main/java/com/xalid/meditsinaproroka/nativeapp'
    reader=root/'Reader.kt'
    reader.write_text(patch_reader(reader.read_text(encoding='utf-8')),encoding='utf-8')
    tests=destination/'app/src/test/java/com/xalid/meditsinaproroka/nativeapp'
    tests.mkdir(parents=True,exist_ok=True)
    (tests/'ImanReaderV7Test.kt').write_text(KOTLIN_TEST,encoding='utf-8')
    old=tests/'ImanReaderV4Test.kt'
    data=old.read_text(encoding='utf-8')
    a='assertEquals("«Они признали господами» [9:31]",example.substring(verse.start,verse.endExclusive))'
    b='assertEquals("«Они признали господами» [9:31]. ",example.substring(verse.start,verse.endExclusive))'
    if data.count(a)!=1:raise RuntimeError('Expected old test assertion unavailable')
    old.write_text(data.replace(a,b,1),encoding='utf-8')
    if list((destination/'app/src/main').rglob('*.pdf')):raise RuntimeError('Unexpected PDF')
    print('v0.7 punctuation fix generated without changing book assets')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--dest',type=Path,required=True);opt=a.parse_args()
    build_v7(Path(__file__).resolve().parents[1],opt.dest)
