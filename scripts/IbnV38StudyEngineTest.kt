package com.xalid.meditsinaproroka.nativeapp

import org.junit.Assert.*
import org.junit.Test

class IbnV38StudyEngineTest {
    @Test fun progressWeightsSourceWordsRatherThanChapterCount() {
        val fractions = listOf(100 to 1f, 900 to .25f)
        assertEquals(.325f, v38WeightedFraction(fractions), 0.0001f)
        assertEquals(0f, v38WeightedFraction(emptyList()), .0001f)
        assertEquals(1f, v38WeightedFraction(listOf(100 to 3f)), .0001f)
    }
    @Test fun streakAllowsInactiveCurrentDayButNotTwoMissedDays() {
        assertEquals(2, v38Streak(listOf(0L, 65_000L, 125_000L, 0L)))
        assertEquals(3, v38Streak(listOf(70_000L, 65_000L, 125_000L, 0L)))
        assertEquals(0, v38Streak(listOf(0L, 0L, 125_000L)))
    }
    @Test fun mixedMemoryReviewCapsQuestionsAndRotatesBetweenChapters() {
        val chapters = listOf("a", "b", "c")
        val counts = mapOf("a" to 4, "b" to 4, "c" to 4)
        val q0 = v38ReviewOrder(chapters, 0, counts)
        val q1 = v38ReviewOrder(chapters, 1, counts)
        assertEquals(10, q0.size)
        assertEquals(10, q1.size)
        assertEquals("a", q0.first().first)
        assertEquals("b", q1.first().first)
        assertTrue(q0.all { it.second in 0..3 })
        assertTrue(v38ReviewOrder(emptyList(), 0, emptyMap()).isEmpty())
    }
}
