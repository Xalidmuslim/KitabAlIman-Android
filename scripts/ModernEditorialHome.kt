package com.xalid.meditsinaproroka.nativeapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BookmarkBorder
import androidx.compose.material.icons.filled.Brightness4
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Editorial home only. Book, reader, storage and 5-tab bottom navigation stay intact.
private val EdPaper=Color(0xFFF7F3EC)
private val EdSurface=Color(0xFFFFFCF7)
private val EdInk=Color(0xFF352D27)
private val EdMuted=Color(0xFF786A5D)
private val EdAccent=Color(0xFF78614C)
private val EdLine=Color(0xFFDDD0BE)
private val EdTrack=Color(0xFFE9DFD1)

@Composable private fun edDark()=MaterialTheme.colorScheme.background.red<0.25f
@Composable private fun edInk()=if(edDark())MaterialTheme.colorScheme.onSurface else EdInk
@Composable private fun edMuted()=if(edDark())MaterialTheme.colorScheme.onSurfaceVariant else EdMuted
@Composable private fun edAccent()=if(edDark())MaterialTheme.colorScheme.primary else EdAccent

@Composable private fun EditorialSurface(
    modifier:Modifier=Modifier,
    onClick:(()->Unit)?=null,
    content:@Composable ColumnScope.()->Unit,
){
    Surface(
        modifier=modifier.then(if(onClick==null)Modifier else Modifier.clickable(onClick=onClick)),
        color=if(edDark())MaterialTheme.colorScheme.surface else EdSurface,
        shape=RoundedCornerShape(15.dp),
        border=BorderStroke(0.75.dp,if(edDark())MaterialTheme.colorScheme.outline else EdLine),
        shadowElevation=0.dp,
    ){Column(content=content)}
}

@Composable private fun EditorialHeader(onSearch:()->Unit,onTheme:()->Unit){
    Row(Modifier.fillMaxWidth().statusBarsPadding()
        .padding(start=18.dp,end=16.dp,top=8.dp,bottom=8.dp),
        verticalAlignment=Alignment.CenterVertically){
        Image(painter=MedicineHomeArtwork.painter(R.drawable.medicine_launcher_book),
            contentDescription=null,modifier=Modifier.size(37.dp),contentScale=ContentScale.Fit)
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)){
            Text("Книга Имана",fontFamily=WebLiterataFont,fontWeight=FontWeight.Bold,
                fontSize=18.sp,color=edInk(),maxLines=1,overflow=TextOverflow.Ellipsis)
            Text("Ибн Таймийя",fontFamily=WebSansFont,fontSize=11.sp,color=edMuted())
        }
        IconButton(onClick=onSearch,modifier=Modifier.size(45.dp)){
            Icon(Icons.Default.Search,contentDescription="Поиск",
                modifier=Modifier.size(21.dp),tint=edInk())
        }
        IconButton(onClick=onTheme,modifier=Modifier.size(45.dp)){
            Icon(Icons.Default.Brightness4,contentDescription="Сменить тему",
                modifier=Modifier.size(20.dp),tint=edInk())
        }
    }
}

@Composable private fun EditorialReadingCard(
    chapterTitle:String,started:Boolean,progressPercent:Int,
    onRead:()->Unit,onStatistics:()->Unit,
){
    EditorialSurface(onClick=onRead){
        Column(Modifier.fillMaxWidth().padding(horizontal=15.dp,vertical=12.dp)){
            Row(verticalAlignment=Alignment.CenterVertically){
                Text(if(started)"ПРОДОЛЖИТЬ ЧТЕНИЕ" else "НАЧАТЬ ЧТЕНИЕ",
                    modifier=Modifier.weight(1f),fontFamily=WebSansFont,fontSize=10.sp,
                    letterSpacing=0.9.sp,fontWeight=FontWeight.SemiBold,color=edMuted())
                Text(progressPercent.toString()+"%",fontFamily=WebSansFont,
                    fontSize=11.sp,fontWeight=FontWeight.Bold,color=edAccent())
            }
            Spacer(Modifier.height(6.dp))
            Row(verticalAlignment=Alignment.CenterVertically){
                Text(chapterTitle,modifier=Modifier.weight(1f),
                    fontFamily=WebLiterataFont,fontSize=16.sp,lineHeight=21.sp,
                    fontWeight=FontWeight.SemiBold,maxLines=2,
                    overflow=TextOverflow.Ellipsis,color=edInk())
                Icon(Icons.Default.ChevronRight,contentDescription="Открыть главу",
                    modifier=Modifier.size(22.dp),tint=edAccent())
            }
            Spacer(Modifier.height(9.dp))
            LinearProgressIndicator(
                progress={ (progressPercent/100f).coerceIn(0f,1f) },
                modifier=Modifier.fillMaxWidth().height(4.dp),
                color=edAccent(),
                trackColor=if(edDark())MaterialTheme.colorScheme.outline else EdTrack,
                drawStopIndicator={},
            )
            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                Text(if(started)"Продолжить с сохранённого места" else "Первая глава",
                    modifier=Modifier.weight(1f),fontFamily=WebSansFont,
                    fontSize=10.sp,color=edMuted(),maxLines=1,
                    overflow=TextOverflow.Ellipsis)
                TextButton(onClick=onStatistics,
                    modifier=Modifier.heightIn(min=44.dp),
                    contentPadding=PaddingValues(horizontal=4.dp)){
                    Text("Прогресс",fontFamily=WebSansFont,fontSize=11.sp,
                        fontWeight=FontWeight.SemiBold,color=edAccent())
                }
            }
        }
    }
}

@Composable private fun EditorialLink(
    title:String,subtitle:String,modifier:Modifier,onClick:()->Unit,
){
    EditorialSurface(modifier.heightIn(min=90.dp),onClick=onClick){
        Column(Modifier.fillMaxWidth().padding(horizontal=12.dp,vertical=11.dp)){
            when(title){
                "Оглавление" -> Icon(Icons.Default.MenuBook,null,
                    modifier=Modifier.size(21.dp),tint=edAccent())
                "Закладки" -> Icon(Icons.Default.BookmarkBorder,null,
                    modifier=Modifier.size(21.dp),tint=edAccent())
                "Подборки" -> Text("▦",fontSize=19.sp,lineHeight=21.sp,color=edAccent())
                else -> Text("Aa",fontFamily=WebLiterataFont,
                    fontSize=18.sp,lineHeight=21.sp,color=edAccent())
            }
            Spacer(Modifier.height(6.dp))
            Text(title,fontFamily=WebSansFont,fontSize=13.sp,
                fontWeight=FontWeight.SemiBold,color=edInk(),maxLines=1)
            Text(subtitle,fontFamily=WebSansFont,fontSize=10.5.sp,
                color=edMuted(),maxLines=1)
        }
    }
}

@Composable private fun EditorialCollectionRow(collection:BookCollection,onClick:()->Unit){
    EditorialSurface(onClick=onClick){
        Row(Modifier.fillMaxWidth().padding(horizontal=13.dp,vertical=9.dp),
            verticalAlignment=Alignment.CenterVertically){
            Column(Modifier.weight(1f)){
                Text(collection.title,fontFamily=WebLiterataFont,fontSize=14.sp,
                    lineHeight=18.sp,fontWeight=FontWeight.SemiBold,
                    color=edInk(),maxLines=1,overflow=TextOverflow.Ellipsis)
                Text(collection.chapterIds.size.toString()+" глав",
                    fontFamily=WebSansFont,fontSize=10.5.sp,color=edMuted())
            }
            Icon(Icons.Default.ChevronRight,null,modifier=Modifier.size(18.dp),
                tint=edMuted())
        }
    }
}

@Composable internal fun ModernEditorialHomeScreen(
    book:BookData,store:AppStore,modifier:Modifier,
    navigate:(Route)->Unit,onGlobalSearch:()->Unit,onToggleTheme:()->Unit,
){
    val chapters=remember(book){book.chapters.filter{it.blocks.isNotEmpty()}}
    val last=store.lastChapterId?.let{id->chapters.firstOrNull{it.id==id}}
    val first=last?:chapters.firstOrNull()
    val fraction=v38WeightedFraction(chapters.map{
        it.blocks.size to chapterReadFraction(it,store)
    })
    val percent=(fraction*100f).toInt().coerceIn(0,100)
    Column(modifier.fillMaxSize().background(
        if(edDark())MaterialTheme.colorScheme.background else EdPaper)){
        EditorialHeader(onSearch=onGlobalSearch,onTheme=onToggleTheme)
        LazyColumn(modifier=Modifier.fillMaxSize(),
            contentPadding=PaddingValues(start=18.dp,end=18.dp,top=4.dp,bottom=114.dp),
            verticalArrangement=Arrangement.spacedBy(11.dp)){
            item(key="quote"){ImanFeaturedQuoteCarousel(navigate)}
            item(key="reading"){
                EditorialReadingCard(
                    chapterTitle=first?.title?:"Предисловие издателя",
                    started=last!=null,progressPercent=percent,
                    onRead={first?.let{navigate(Route.Reader(it.id,resume=last!=null))}},
                    onStatistics={navigate(Route.Progress)},
                )
            }
            item(key="sections-title"){
                Text("Разделы",modifier=Modifier.padding(top=3.dp),
                    fontFamily=WebLiterataFont,fontSize=20.sp,
                    fontWeight=FontWeight.Bold,color=edInk())
            }
            item(key="links-first"){
                Row(horizontalArrangement=Arrangement.spacedBy(9.dp)){
                    EditorialLink("Оглавление",chapters.size.toString()+" глав",
                        Modifier.weight(1f)){navigate(Route.Book)}
                    EditorialLink("Подборки",book.collections.size.toString()+" разделов",
                        Modifier.weight(1f)){navigate(Route.Collections)}
                }
            }
            item(key="links-second"){
                Row(horizontalArrangement=Arrangement.spacedBy(9.dp)){
                    EditorialLink("Понятия",book.glossary.size.toString()+" терминов",
                        Modifier.weight(1f)){navigate(Route.Glossary)}
                    EditorialLink("Закладки",store.bookmarks.size.toString()+" сохранено",
                        Modifier.weight(1f)){navigate(Route.Bookmarks)}
                }
            }
            item(key="collection-heading"){
                Row(verticalAlignment=Alignment.CenterVertically){
                    Text("Быстрые подборки",modifier=Modifier.weight(1f),
                        fontFamily=WebLiterataFont,fontSize=19.sp,
                        fontWeight=FontWeight.Bold,color=edInk())
                    TextButton(onClick={navigate(Route.Collections)},
                        modifier=Modifier.heightIn(min=44.dp)){
                        Text("Все",fontFamily=WebSansFont,fontSize=12.sp,color=edAccent())
                    }
                }
            }
            items(book.collections.take(3),key={"ed:"+it.id}){collection->
                EditorialCollectionRow(collection){
                    navigate(Route.CollectionDetail(collection.id))
                }
            }
        }
    }
}
